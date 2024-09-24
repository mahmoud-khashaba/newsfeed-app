import mysql.connector
from mysql.connector import errorcode

# Database configuration
config = {
    'user': 'root',
    'password': 'password',
    'host': '127.0.0.1',  # or 'localhost'
}

# Database name
DB_NAME = 'newsfeed'

# Connect to MySQL server
try:
    cnx = mysql.connector.connect(**config)
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
