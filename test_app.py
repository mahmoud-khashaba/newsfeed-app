import pytest
import json

from app import app as flask_app
from app import create_app
from app import get_db_connection
import time
from mysql.connector import errors
from config import config
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def reset_database():
    max_retries = 5
    retry_delay = 2  

    for attempt in range(max_retries):
        try:
            logging.debug("Attempting to reset database, attempt %d", attempt + 1)
            connection = get_db_connection()
            if connection is None:
                logging.error("Database connection failed")
                return

            cursor = connection.cursor()
            cursor.execute("DELETE FROM User")
            cursor.execute("DELETE FROM Post")
            cursor.execute("DELETE FROM Profile")
            cursor.execute("DELETE FROM Comment")
            cursor.execute("DELETE FROM `Like`")
            cursor.execute("DELETE FROM Share")
            cursor.execute("DELETE FROM Follow")
            cursor.execute("DELETE FROM Tag")
            cursor.execute("DELETE FROM PostTag")
            cursor.execute("DELETE FROM Message")
            connection.commit()
            cursor.close()
            connection.close()
            logging.debug("Database reset successfully")
            break  # Exit the loop if the query is successful
        except errors.DatabaseError as err:
            logging.error("Database error: %s", err)
            if err.errno == 1205:  # Lock wait timeout exceeded
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise
            else:
                raise

def add_test_user():
    connection = get_db_connection()
    if connection is None:
        print("Database connection failed")
        return

    cursor = connection.cursor()
    cursor.execute("INSERT INTO User (id, username, email, password) VALUES (1, 'testuser', 'testuser@example.com', 'password')")
    cursor.execute("INSERT INTO User (id, username, email, password) VALUES (2, 'testuser2', 'testuser2@example.com', 'password')")
    connection.commit()
    cursor.close()
    connection.close()
def add_test_post():
    connection = get_db_connection()
    if connection is None:
        print("Database connection failed")
        return

    cursor = connection.cursor()
    cursor.execute("INSERT INTO Post (id, user_id, content) VALUES (1, 1, 'This is a test post')")
    connection.commit()
    cursor.close()
    connection.close()

def add_test_tag():
    connection = get_db_connection()
    if connection is None:
        print("Database connection failed")
        return

    cursor = connection.cursor()
    cursor.execute("INSERT INTO Tag (id, name) VALUES (1, 'Tag')")
    connection.commit()
    cursor.close()
    connection.close()

@pytest.fixture(autouse=True)
def setup_database():
    reset_database()
    add_test_user()
    add_test_post()
    add_test_tag()

def test_add_post(client):
    url = "/post"
    data = {
        "id": 2,
        "user_id": 1,
        "content": "This is a test post 2"
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Post added successfully'


def test_get_post(client):
    post_id = 1
    url = f"/post/{post_id}"
    response = client.get(url)
    assert response.status_code == 200

def test_update_post(client):
    post_id = 1
    url = f"/post/{post_id}"
    data = {
        "content": "This is an updated test post"
    }
    response = client.put(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    assert response.json['message'] == 'Post updated successfully'

def test_add_profile(client):
    url = "/profile"
    data = {
        "user_id": 1,
        "username": "unique_testuser_1",
        "bio": "This is a test bio",
        "profile_picture": "http://example.com/pic.jpg"
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Profile added successfully'

def test_add_comment(client):
    url = "/comment"
    data = {
        "post_id": 1,
        "user_id": 1,
        "content": "This is a test comment"
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Comment added successfully'

def test_add_like(client):
    url = "/like"
    data = {
        "post_id": 1,
        "user_id": 1
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Like added successfully'

def test_add_share(client):
    url = "/share"
    data = {
        "post_id": 1,
        "user_id": 1
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Share added successfully'

def test_add_follow(client):
    url = "/follow"
    data = {
        "follower_id": 1,
        "followee_id": 2
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Follow added successfully'

def test_add_tag(client):
    url = "/tag"
    data = {
        "name": "test_tag"
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Tag added successfully'

def test_add_post_tag(client):
    url = "/posttag"
    data = {
        "post_id": 1,
        "tag_id": 1
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'PostTag added successfully'

def test_add_message(client):
    # Setup: Ensure the sender and receiver exist in the User table
    user_data = {"id": 2, "username": "Sender", "email": "sender@example.com", "password": "password"}
    
    # Check if the user already exists
    response = client.get(f"/user/{user_data['id']}")
    if response.status_code == 404:
        response = client.post("/user", data=json.dumps(user_data), content_type='application/json')
        assert response.status_code == 201  # Check if the user was created successfully
    
    # Proceed with the rest of the test
    url = "/message"
    data = {
        "sender_id": 1,
        "receiver_id": 2,
        "content": "This is a test message"
    }
    response = client.post(url, data=json.dumps(data), content_type='application/json')
    assert response.status_code == 201
    assert response.json['message'] == 'Message sent successfully'

def test_delete_post(client):
    post_id = 1
    url = f"/post/{post_id}"
    response = client.delete(url)
    assert response.status_code == 200
    assert response.json['message'] == 'Post deleted successfully'

