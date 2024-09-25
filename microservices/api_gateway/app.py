from flask import Flask, request, jsonify
import requests
import pika
import json
import logging
from consul import Consul
from pybreaker import CircuitBreaker
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps

app = Flask(__name__)
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'secret-key'  

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure rate limiting
if app.config.get('RATELIMIT_ENABLED', True):
    limiter = Limiter(
        key_func=get_remote_address,  # Specify key_func only once
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )
else:
    limiter = None

# Consul configuration
consul_client = Consul(host="localhost", port=8500)

# RabbitMQ configuration
RABBITMQ_HOST = 'localhost'
RABBITMQ_QUEUE = 'service_queue'

# Circuit breaker configuration
breaker = CircuitBreaker(fail_max=5, reset_timeout=30)

def get_service_url(service_name):
    _, services = consul_client.health.service(service_name, passing=True)
    if services:
        return f"http://{services[0]['Service']['Address']}:{services[0]['Service']['Port']}"
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

@breaker
def make_request(method, url, **kwargs):
    return requests.request(method, url, **kwargs)

def jwt_required_with_args():
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            return fn(*args, **kwargs)
        return decorated
    return wrapper

@app.route('/api/v1/<service>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@jwt_required_with_args()
def gateway(service, path):
    service_url = get_service_url(service)
    if not service_url:
        return jsonify({"error": "Service not found"}), 404

    url = f"{service_url}/{path}"
    try:
        response = make_request(
            method=request.method,
            url=url,
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=5
        )

        publish_message({
            'service': service,
            'path': path,
            'method': request.method,
            'status_code': response.status_code
        })

        return (
            response.content,
            response.status_code,
            response.headers.items()
        )
    except requests.Timeout:
        logger.error(f"Request to {service} timed out")
        return jsonify({"error": "Service timeout"}), 504
    except requests.ConnectionError:
        logger.error(f"Connection error to {service}")
        return jsonify({"error": "Service unavailable"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in gateway: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username == 'admin' and password == 'password':
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"error": "Bad username or password"}), 401

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)