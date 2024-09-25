import pytest
from app import app, limiter
from flask_jwt_extended import create_access_token
from unittest.mock import patch
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import time
from flask import current_app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_consul():
    with patch('app.get_service_url') as mock:
        yield mock

@pytest.fixture
def mock_requests():
    with patch('app.make_request') as mock:
        yield mock

@pytest.fixture
def no_limiter(monkeypatch):
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

    monkeypatch.setattr('flask_limiter.Limiter', DummyLimiter)
    yield
    monkeypatch.undo()

@pytest.fixture
def disable_rate_limit(monkeypatch):
    def dummy_limit(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

    monkeypatch.setattr('flask_limiter.Limiter.limit', dummy_limit)
    monkeypatch.setattr('flask_limiter.Limiter.enabled', False)
    yield
    monkeypatch.undo()

@pytest.fixture
def disable_rate_limit():
    with patch('flask_limiter.Limiter.exempt', return_value=True):
        yield

def create_limiter(app):
    return Limiter(
        app,
        key_func=get_remote_address,
        storage_uri="memory://",  # Use appropriate storage for your needs
        default_limits=["200 per day", "50 per hour"]
    )

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

def test_login_success(client):
    response = client.post('/login', json={"username": "admin", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json

def test_login_failure(client):
    response = client.post('/login', json={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401
    assert response.json == {"error": "Bad username or password"}

def test_gateway_service_not_found(client, mock_consul):
    mock_consul.return_value = None
    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/api/v1/nonexistent_service/test', headers=headers)
    assert response.status_code == 404
    assert response.json == {"error": "Service not found"}

def test_gateway_service_success(client, mock_consul, mock_requests):
    mock_consul.return_value = "http://user-service:5001"
    mock_requests.return_value.status_code = 200
    mock_requests.return_value.content = b'{"id": 1, "username": "testuser"}'
    mock_requests.return_value.headers = {'Content-Type': 'application/json'}
    
    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/api/v1/user-service/user/1', headers=headers)
    
    assert response.status_code == 200
    assert response.json == {"id": 1, "username": "testuser"}

def test_gateway_service_timeout(client, mock_consul, mock_requests):
    mock_consul.return_value = "http://user-service:5001"
    mock_requests.side_effect = requests.Timeout("Request timed out")
    
    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/api/v1/user-service/user/1', headers=headers)
    
    assert response.status_code == 504
    assert response.json == {"error": "Service timeout"}

def test_gateway_service_connection_error(client, mock_consul, mock_requests):
    mock_consul.return_value = "http://user-service:5001"
    mock_requests.side_effect = requests.ConnectionError("Connection failed")
    
    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/api/v1/user-service/user/1', headers=headers)
    
    assert response.status_code == 503
    assert response.json == {"error": "Service unavailable"}

def test_rate_limiting(client, mock_consul, mock_requests):
    mock_consul.return_value = "http://user-service:5001"
    mock_requests.return_value.status_code = 200
    mock_requests.return_value.content = b'{"id": 1, "username": "testuser"}'
    mock_requests.return_value.headers = {'Content-Type': 'application/json'}

    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}

    # Make 101 requests (1 over the limit)
    for i in range(101):
        response = client.get('/api/v1/user-service/user/1', headers=headers)
        if i == 100:  # Print info for the last request
            print(f"Final request status code: {response.status_code}")
            print(f"Final request data: {response.get_data(as_text=True)}")

    assert response.status_code == 429
    assert "Too Many Requests" in response.get_data(as_text=True), f"Expected 'Too Many Requests' in response, but got: {response.get_data(as_text=True)}"


def test_unauthorized_access(client, mock_consul):
    mock_consul.return_value = "http://user-service:5001"
    
    # Reset rate limiter before the test
    with app.app_context():
        limiter.reset()
    
    response = client.get('/api/v1/user-service/user/1')
    assert response.status_code == 401
    assert "Missing Authorization Header" in response.json["msg"]


