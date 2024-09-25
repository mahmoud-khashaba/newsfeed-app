import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
import logging
from db.config import config
import pika
import json
from consul import Consul
from pybreaker import CircuitBreaker
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import redis
import consul

app = Flask(__name__)
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'secret-key'  

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

# RabbitMQ configuration
RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'service_queue'

# Consul configuration
consul_client = Consul(host="localhost", port=8500)

# Redis configuration
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Circuit breaker configuration
breaker = CircuitBreaker(fail_max=5, reset_timeout=30)

@breaker
def get_db_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        return None

def publish_message(message):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        connection.close()
        logger.info(f"Message published to queue: {message}")
    except Exception as e:
        logger.error(f"Error publishing message to RabbitMQ: {str(e)}")

@app.route('/api/v1/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    # Try to get user from cache
    cached_user = redis_client.get(f"user:{user_id}")
    if cached_user:
        return jsonify(json.loads(cached_user)), 200

    cnx = get_db_connection()
    if cnx is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = cnx.cursor(dictionary=True)
        query = "SELECT * FROM User WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        cnx.close()

        if user:
            result = {
                "id": user['id'],
                "username": user['username'],
                "email": user['email']
            }
            # Cache the user for future requests
            redis_client.setex(f"user:{user_id}", 3600, json.dumps(result))  # Cache for 1 hour
            publish_message({"action": "get_user", "user_id": user_id, "status": "success"})
            return jsonify(result), 200
        else:
            publish_message({"action": "get_user", "user_id": user_id, "status": "not_found"})
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        publish_message({"action": "get_user", "user_id": user_id, "status": "error", "message": str(e)})
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/api/v1/user', methods=['POST'])
@jwt_required()
def add_user():
    user_data = request.json
    try:
        cnx = get_db_connection()
        if cnx is None:
            return jsonify({"error": "Database connection failed"}), 500

        cursor = cnx.cursor()
        add_user_query = ("INSERT INTO User (username, email, password) "
                          "VALUES (%s, %s, %s)")
        cursor.execute(add_user_query, (user_data['username'], user_data['email'], user_data['password']))
        cnx.commit()
        cursor.close()
        cnx.close()
        
        publish_message({"action": "add_user", "user_id": cursor.lastrowid, "status": "success"})
        return jsonify({"message": "User created successfully"}), 201
    except mysql.connector.IntegrityError:
        return jsonify({"error": "User already exists"}), 409
    except Exception as e:
        return jsonify({"error": "An error occurred while creating the user"}), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

def register_service():
    consul_client.agent.service.register(
        "user-service",
        service_id="user-service-1",
        address="localhost",
        port=5001,
        check=consul.Check.http(url="http://localhost:5001/health", interval="10s", timeout="5s")
    )

if __name__ == '__main__':
    register_service()
    app.run(debug=True, port=5001)