import mysql.connector
from mysql.connector import Error
from db.config import config

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        return connection
    except mysql.connector.Error as err:
        print(f"The error '{err}' occurred")
        return None

def execute_script_from_file(filename, connection):
    with open(filename, 'r') as file:
        script = file.read()
    
    cursor = connection.cursor()
    try:
        for result in cursor.execute(script, multi=True):
            if result.with_rows:
                print(f"Rows produced by statement '{result.statement}':")
                print(result.fetchall())
            else:
                print(f"Number of rows affected by statement '{result.statement}': {result.rowcount}")
        connection.commit()
    except Error as e:
        print(f"Error: '{e}'")
        connection.rollback()
    finally:
        cursor.close()

def main():
    connection = get_db_connection()
    if connection is None:
        print("Database connection failed")
        return

    try:
        execute_script_from_file('schema.sql', connection)
        print("Schema migrated successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    main()
