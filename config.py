import os
from datetime import timedelta
class Config:
    # Core Security
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))
    TEST_TOKEN_SECRET = os.getenv('TEST_TOKEN_SECRET')

    # MySQL Configuration
    DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')
    DATABASE_USER = os.environ.get('DATABASE_USER', 'root')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'your_mysql_password')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'your_database_name')

    # Mail Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'

    # Razorpay Configuration
    RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
    RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

    # google OAuth
    GOOGLE_CLIENT_ID = os.getenv("CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("CLIENT_SECRET")
    REDIRECT_URI = os.getenv("REDIRECT_URI")

    # Email Rate Limiting 
    EMAIL_RATE_LIMIT = '5/hour'

    # Token Expiry
    RECEIPT_TOKEN_EXPIRY_SECONDS = 300
    
    # Session Security
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Lax'
