from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import logging
from db.config import config

def create_app():
    app = Flask(__name__)
    # ... additional app configuration ...
    return app

app = create_app()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Database configuration
config = {
    'user': config['user'],
    'password': config['password'],
    'host': config['host'],
    'database': config['database']
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**config)
        return connection
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return None

def get_user_by_id(user_id):
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return None

    try:
        cursor = cnx.cursor(dictionary=True)
        query = "SELECT * FROM User WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        cnx.close()
        return user
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return None
    finally:
        if cnx:
            cnx.close()

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = get_user_by_id(user_id)
    if user:
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email
            # Add other fields as necessary
        }), 200
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/post', methods=['POST'])
def add_post():
    logging.debug("Received request to add post")
    try:
        data = request.get_json()
        logging.debug(f"Request data: {data}")
        id = data['id']
        user_id = data['user_id']
        content = data['content']
                
        # Connect to the database
        cnx = get_db_connection()
        if cnx is None:
            logging.error("Database connection failed")
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = cnx.cursor()
        
        # Insert the post into the database
        add_post_query = ("INSERT INTO Post (id, user_id, content) "
                          "VALUES (%s, %s, %s)")
        cursor.execute(add_post_query, (id, user_id, content))
        
        # Commit the transaction
        cnx.commit()
        
        # Close the cursor and connection
        cursor.close()
        cnx.close()
        
        logging.debug("Post added successfully")
        return jsonify({'message': 'Post added successfully'}), 201
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({'error': 'Internal Server Error'}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/post/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    logging.debug(f"Received request to update post with id {post_id}")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    content = data['content']
    
    # Connect to the database
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = cnx.cursor()
    
    try:
        # Update the post in the database
        update_post_query = "UPDATE Post SET content = %s WHERE id = %s"
        cursor.execute(update_post_query, (content, post_id))
        cnx.commit()
        logging.debug("Post updated successfully")

        # Close the cursor and connection
        cursor.close()
        cnx.close()
        
        return jsonify({'message': 'Post updated successfully'}), 200
    except mysql.connector.Error as err:
        logging.error(f"Database error: {err}")
        return jsonify({'error': 'Internal Server Error'}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    logging.debug(f"Received request to delete post with id {post_id}")
    
    # Connect to the database
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM Post WHERE id = %s", (post_id,))
        cnx.commit()
        logging.debug("Post deleted successfully")
        return jsonify({'message': 'Post deleted successfully'}), 200
    except Exception as e:
        logging.error(f"Error deleting post: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/post/<int:id>', methods=['GET'], endpoint='get_post_by_id')
def get_post(id):
    logging.debug(f"Received request to get post with ID: {id}")
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM Post WHERE id = %s", (id,))
        post = cursor.fetchone()
        if post is None:
            logging.debug(f"Post with ID {id} not found")
            return jsonify({'error': 'Post not found'}), 404
        logging.debug(f"Post with ID {id} found: {post}")
        return jsonify({'post': post}), 200
    except Exception as e:
        logging.error(f"Error retrieving post: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/profile', methods=['POST'])
def add_profile():
    logging.debug("Received request to add profile")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    user_id = data['user_id']
    bio = data.get('bio', '')
    profile_picture = data.get('profile_picture', '')
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO Profile (user_id, bio, profile_picture) VALUES (%s, %s, %s)", (user_id, bio, profile_picture))
        cnx.commit()
        logging.debug("Profile added successfully")
        return jsonify({'message': 'Profile added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding profile: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/comment', methods=['POST'])
def add_comment():
    logging.debug("Received request to add comment")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    post_id = data['post_id']
    user_id = data['user_id']
    content = data['content']
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO Comment (post_id, user_id, content) VALUES (%s, %s, %s)", (post_id, user_id, content))
        cnx.commit()
        logging.debug("Comment added successfully")
        return jsonify({'message': 'Comment added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding comment: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/like', methods=['POST'])
def add_like():
    logging.debug("Received request to add like")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    post_id = data['post_id']
    user_id = data['user_id']
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO `Like` (post_id, user_id) VALUES (%s, %s)", (post_id, user_id))
        cnx.commit()
        logging.debug("Like added successfully")
        return jsonify({'message': 'Like added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding like: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/share', methods=['POST'])
def add_share():
    logging.debug("Received request to add share")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    post_id = data['post_id']
    user_id = data['user_id']
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO Share (post_id, user_id) VALUES (%s, %s)", (post_id, user_id))
        cnx.commit()
        logging.debug("Share added successfully")
        return jsonify({'message': 'Share added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding share: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/follow', methods=['POST'])
def add_follow():
    logging.debug("Received request to add follow")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    follower_id = data['follower_id']
    followee_id = data['followee_id']
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO Follow (follower_id, followee_id) VALUES (%s, %s)", (follower_id, followee_id))
        cnx.commit()
        logging.debug("Follow added successfully")
        return jsonify({'message': 'Follow added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding follow: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/tag', methods=['POST'])
def add_tag():
    logging.debug("Received request to add tag")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    name = data['name']
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO Tag (name) VALUES (%s)", (name,))
        cnx.commit()
        logging.debug("Tag added successfully")
        return jsonify({'message': 'Tag added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding tag: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/posttag', methods=['POST'])
def add_post_tag():
    logging.debug("Received request to add post tag")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    post_id = data['post_id']
    tag_id = data['tag_id']
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO PostTag (post_id, tag_id) VALUES (%s, %s)", (post_id, tag_id))
        cnx.commit()
        logging.debug("PostTag added successfully")
        return jsonify({'message': 'PostTag added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding post tag: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/message', methods=['POST'])
def add_message():
    logging.debug("Received request to add message")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    
    sender_id = data['sender_id']
    receiver_id = data['receiver_id']
    content = data['content']
    
    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO Message (sender_id, receiver_id, content) VALUES (%s, %s, %s)", (sender_id, receiver_id, content))
        cnx.commit()
        logging.debug("Message added successfully")
        return jsonify({'message': 'Message sent successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding message: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

@app.route('/user', methods=['POST'])
def add_user():
    logging.debug("Received request to add user")
    data = request.get_json()
    logging.debug(f"Request data: {data}")
    id = data['id']
    username = data['username']
    email = data['email']
    password = data['password']

    cnx = get_db_connection()
    if cnx is None:
        logging.error("Database connection failed")
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO User (id, username, email, password) VALUES (%s, %s, %s, %s)", (id, username, email, password))
        cnx.commit()
        logging.debug("User added successfully")
        return jsonify({'message': 'User added successfully'}), 201
    except Exception as e:
        logging.error(f"Error adding user: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cnx.close()
            logging.debug("Database connection closed")

if __name__ == '__main__':
    app.run(debug=True)
