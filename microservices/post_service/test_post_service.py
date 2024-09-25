import pytest
from app import app, get_db_connection
import json
import mysql.connector
from unittest.mock import patch, MagicMock
import logging
import time
from mysql.connector import errors

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

def reset_database():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE TABLE User")
    cursor.execute("TRUNCATE TABLE Post")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    connection.commit()
    cursor.close()
    connection.close()

def add_test_user():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO User (username, email, password) VALUES ('testuser', 'testuser@example.com', 'password')")
    user_id = cursor.lastrowid
    connection.commit()
    cursor.close()
    connection.close()
    return user_id

def add_test_post(user_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO Post (id, user_id, content, created_at) VALUES (%s, %s, %s, %s)", (200,user_id, "This is a test post", "2024-02-20 12:00:00"))
    post_id = cursor.lastrowid
    connection.commit()
    cursor.close()
    connection.close()
    return post_id


@pytest.fixture(autouse=True)
def setup_database():
    reset_database()
    user_id = add_test_user()
    post_id = add_test_post(user_id)
    return user_id, post_id

def test_add_post_success(setup_database,client):
    user_id, post_id = setup_database
    post_data = {
        "user_id": user_id,
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
    
    assert response.status_code == 201
    assert json.loads(response.get_data(as_text=True)) == {"id": response.json['id'], "message": "Post added successfully"}

    

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


def test_get_post_success(client, setup_database):
    user_id, post_id = setup_database
    mock_post = (post_id, user_id, "This is a test post", "2024-02-20 12:00:00")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = mock_post
    mock_conn.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor


    with patch('microservices.post_service.app.get_db_connection', return_value=mock_conn):
        response = client.get(f'/post/{post_id}')

    assert response.status_code == 200
    assert json.loads(response.get_data(as_text=True)) == {
        "id": post_id,
        "user_id": user_id,
        "content": "This is a test post",
        "created_at": "2024-02-20 12:00:00"
    }