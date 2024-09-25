import os
import sys
from flask import Flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the Flask apps from each service
from microservices.api_gateway.app import app as api_gateway_app
from microservices.user_service.app import app as user_service_app
from microservices.post_service.app import app as post_service_app

# Create the main Flask app
app = Flask(__name__)

# Configure the DispatcherMiddleware
application = DispatcherMiddleware(app, {
    '/api': api_gateway_app,
    '/user': user_service_app,
    '/post': post_service_app
})

if __name__ == '__main__':
    # Run the application
    run_simple('localhost', 5000, application, use_reloader=True, use_debugger=True, use_evalex=True)