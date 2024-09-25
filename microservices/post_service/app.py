import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Flask, request, jsonify
import mysql.connector
import logging
from db.config import config


app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
db_config = {
    'user': config['user'],
    'password': config['password'],
    'host': config['host'],
    'database': config['database']
}

def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        return None

@app.route('/post', methods=['POST'])
def add_post():
    logger.info("Received request to add post")
    try:
        data = request.get_json()
        user_id = data['user_id']
        content = data['content']
                
        cnx = get_db_connection()
        if cnx is None:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = cnx.cursor()
        
        add_post_query = ("INSERT INTO Post (user_id, content) "
                          "VALUES (%s, %s)")
        cursor.execute(add_post_query, (user_id, content))
        
        post_id = cursor.lastrowid
        
        cnx.commit()
        cursor.close()
        cnx.close()
        
        logger.info(f"Post added successfully with id: {post_id}")
        return jsonify({'message': 'Post added successfully', 'post_id': post_id}), 201
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/post/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    logger.info(f"Received request to update post with id {post_id}")
    data = request.get_json()
    content = data['content']
    
    cnx = get_db_connection()
    if cnx is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = cnx.cursor()
    
    try:
        update_post_query = "UPDATE Post SET content = %s WHERE id = %s"
        cursor.execute(update_post_query, (content, post_id))
        cnx.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Post not found'}), 404
        
        logger.info("Post updated successfully")
        return jsonify({'message': 'Post updated successfully'}), 200
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        cursor.close()
        cnx.close()

@app.route('/post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    logger.info(f"Received request to delete post with id {post_id}")
    
    cnx = get_db_connection()
    if cnx is None:
        return jsonify({'error': 'Database connection failed'}), 500

    try:
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM Post WHERE id = %s", (post_id,))
        cnx.commit()
        
        if cursor.rowcount == 0:
            return jsonify({'error': 'Post not found'}), 404
        
        logger.info("Post deleted successfully")
        return jsonify({'message': 'Post deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        if cnx:
            cursor.close()
            cnx.close()

@app.route('/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Post WHERE id = %s", (post_id,))
        post = cursor.fetchone()
        if post:
            return jsonify({
                'id': post[0],
                'user_id': post[1],
                'content': post[2],
                'created_at': post[3].strftime('%Y-%m-%d %H:%M:%S')
            }), 200
        else:
            return jsonify({'message': 'Post not found'}), 404
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5002)