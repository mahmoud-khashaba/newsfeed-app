import mysql.connector
from mysql.connector import errorcode
from config import config

# Ensure all required keys are present in the config
required_keys = ['user', 'password', 'host', 'database']
for key in required_keys:
    if key not in config:
        raise KeyError(f"Missing required config key: {key}")

# Database configuration
db_config = {
    'user': config['user'],
    'password': config['password'],
    'host': config['host'],
}

# Database name
DB_NAME = config['database']

# Connect to MySQL server
try:
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    print("Connected to MySQL server")

    # Create database
    try:
        cursor.execute(f"CREATE DATABASE {DB_NAME}")
        print(f"Database {DB_NAME} created successfully")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DB_CREATE_EXISTS:
            print(f"Database {DB_NAME} already exists.")
        else:
            print(f"Failed to create database {DB_NAME}: {err}")
    
    # Close cursor and connection
    cursor.close()
    cnx.close()
    print("MySQL connection closed")

except mysql.connector.Error as err:
    print(f"Error: {err}")
except ModuleNotFoundError as err:
    print(f"Module not found: {err}. Please ensure 'mysql-connector-python' is installed.")
