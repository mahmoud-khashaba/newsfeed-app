from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import logging

app = Flask(__name__)

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='newsfeed',
            user='root',
            password='password'
        )
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

@app.route('/post', methods=['POST'])
def add_post():
    data = request.get_json()
    user_id = data['user_id']
    content = data['content']
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO Post (user_id, content) VALUES (%s, %s)", (user_id, content))
    connection.commit()
    return jsonify({'message': 'Post added successfully'}), 201

@app.route('/post/<int:post_id>', methods=['PUT'])
def update_post(post_id):
    data = request.get_json()
    content = data['content']
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE Post SET content = %s WHERE post_id = %s", (content, post_id))
    connection.commit()
    return jsonify({'message': 'Post updated successfully'}), 200

@app.route('/post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM Post WHERE post_id = %s", (post_id,))
    connection.commit()
    return jsonify({'message': 'Post deleted successfully'}), 200

@app.route('/post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Post WHERE post_id = %s", (post_id,))
    post = cursor.fetchone()
    if post:
        return jsonify({'post_id': post[0], 'user_id': post[1], 'content': post[2], 'created_at': post[3]}), 200
    else:
        return jsonify({'message': 'Post not found'}), 404

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)