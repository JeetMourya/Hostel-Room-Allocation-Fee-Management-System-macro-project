import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'hostel_user')
        self.password = os.getenv('DB_PASSWORD', 'hostel123')
        self.database = os.getenv('DB_NAME', 'hostel_db')
        self.connection = None
        
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=3306
            )
            return self.connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        connection = self.connect()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, params or ())
                
                if query.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                else:
                    connection.commit()
                    result = cursor.lastrowid
                
                cursor.close()
                return result
            except Error as e:
                print(f"Error executing query: {e}")
                return None
            finally:
                self.disconnect()
        return None
    
    def health_check(self):
        try:
            connection = self.connect()
            if connection and connection.is_connected():
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return True
        except Error:
            return False
        finally:
            self.disconnect()
        return False

# Create global database instance
db = Database()

# Test connection
if __name__ == "__main__":
    if db.health_check():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
