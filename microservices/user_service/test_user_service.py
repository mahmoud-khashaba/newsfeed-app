import pytest
from app import app, get_db_connection
from flask_jwt_extended import create_access_token
import json
import mysql.connector

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db(mocker):
    mock_connection = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_connection.cursor.return_value = mock_cursor
    mocker.patch('app.get_db_connection', return_value=mock_connection)
    return mock_cursor

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

def test_get_user_success(client, mock_db):
    mock_db.fetchone.return_value = {"id": 1, "username": "testuser", "email": "test@example.com"}
    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/api/v1/user/1', headers=headers)
    assert response.status_code == 200
    assert response.json == {"id": 1, "username": "testuser", "email": "test@example.com"}

def test_get_user_not_found(client, mock_db):
    mock_db.fetchone.return_value = None
    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get('/api/v1/user/999', headers=headers)
    assert response.status_code == 404
    assert response.json == {"error": "User not found"}

def test_add_user_success(client, mock_db):
    mock_cursor = mock_db.return_value.cursor.return_value
    mock_cursor.lastrowid = 1
    with app.app_context():
        access_token = create_access_token(identity="test")
    headers = {"Authorization": f"Bearer {access_token}"}
    user_data = {"username": "newuser", "email": "new@example.com", "password": "password123"}
    response = client.post('/api/v1/user', headers=headers, json=user_data)
    assert response.status_code == 201
    assert response.json == {'message': 'User created successfully'}
