import pytest
from app import app, get_db_connection
import json
import mysql.connector
from unittest.mock import patch, MagicMock

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

def test_add_post_success(client):
    post_data = {
        "user_id": 1,
        "content": "This is a test post"
    }

    # Create a mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.lastrowid = 1
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Patch the get_db_connection function
    with patch('microservices.post_service.app.get_db_connection', return_value=mock_conn):
        response = client.post('/post', json=post_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response data: {response.get_data(as_text=True)}")

    assert response.status_code == 201
    assert json.loads(response.get_data(as_text=True)) == {"id": 1, "message": "Post added successfully"}

    # Verify that execute was called with the correct parameters
    mock_cursor.execute.assert_called_once_with(
        'INSERT INTO posts (user_id, content) VALUES (?, ?)',
        (post_data['user_id'], post_data['content'])
    )

def test_add_post_db_error(client, mock_db):
    mock_db.side_effect = mysql.connector.Error("Database error")

    post_data = {
        "user_id": 1,
        "content": "This is a test post"
    }
    response = client.post('/post', json=post_data)
    assert response.status_code == 500
    assert response.json == {"error": "Internal Server Error"}

def test_update_post_success(client, mock_db):
    mock_cursor = mock_db.return_value
    mock_cursor.rowcount = 1

    post_data = {
        "content": "This is an updated test post"
    }
    response = client.put('/post/1', json=post_data)
    assert response.status_code == 200
    assert response.json == {"message": "Post updated successfully"}

def test_delete_post_success(client, mock_db):
    mock_cursor = mock_db.return_value
    mock_cursor.rowcount = 1

    response = client.delete('/post/1')
    assert response.status_code == 200
    assert response.json == {"message": "Post deleted successfully"}


def test_get_post_success(client):
    mock_post = (1, 1, "This is a test post", "2023-05-01 12:00:00")

    # Create a mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = mock_post
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Mock the execute method with the expected query
    mock_cursor.execute = MagicMock()

    # Patch the get_db_connection function
    with patch('microservices.post_service.app.get_db_connection', return_value=mock_conn):
        response = client.get('/post/1')
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.get_data(as_text=True)}")

    # Check if the correct query was executed
    print(f"Execute called: {mock_cursor.execute.call_count} times")
    print(f"Execute call args: {mock_cursor.execute.call_args}")
    mock_cursor.execute.assert_called_once_with("SELECT * FROM posts WHERE id = ?", (1,))

    # Assert the response
    assert response.status_code == 200
    assert json.loads(response.get_data(as_text=True)) == {
        'id': 1,
        'user_id': 1,
        'content': "This is a test post",
        'created_at': "2023-05-01 12:00:00"
    }
