import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        f"mysql+mysqlconnector://{os.getenv('DB_USER', 'hostel_user')}:{os.getenv('DB_PASSWORD', 'hostel123')}@{os.getenv('DB_HOST', 'localhost')}:3306/{os.getenv('DB_NAME', 'hostel_db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt_secret_key')
    JWT_ACCESS_TOKEN_EXPIRES = 3600 # 1 hour
