import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secure-secret-key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Disable SQL query logging in production
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')

    # Mobile money API credentials (replace with actual provider details)
    MOMO_API_USER_ID = os.getenv('MOMO_API_USER_ID')
    MOMO_API_KEY = os.getenv('MOMO_API_KEY', 'sandbox-key')
    MOMO_API_SECRET = os.getenv('MOMO_API_SECRET', 'sandbox-secret')
    MOMO_BASE_URL = os.getenv('MOMO_BASE_URL', 'https://sandbox.momoapi.com')

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URI', 'sqlite:///dev.db')
    SQLALCHEMY_ECHO = True  # Log SQL queries for debugging

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://user:pass@localhost/prod_db')
    SQLALCHEMY_POOL_SIZE = 20  # Connection pool size for scalability
    SQLALCHEMY_MAX_OVERFLOW = 10  # Allow extra connections under load

# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
