import os
from dotenv import load_dotenv

# --------------------------------------------------------------------------
# Load variables from .env file into the operating system environment
# --------------------------------------------------------------------------
load_dotenv()

class Config:
    """
    Central Configuration class for EduConnect.
    
    Reads sensitive credentials from environment variables.
    If an environment variable is not set, it falls back to safe local defaults.
    """
    # Secret key used for session signing and CSRF protection
    SECRET_KEY = os.getenv('SECRET_KEY', 'educonnect-local-dev-secret-key-2026')

    # MySQL Database Connection Details
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'educonnect_db')

    # Optional AI Assistant API Key (Gemini)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    # Server Port & Debug Mode
    # In cloud hosting (Render, Railway, Heroku), PORT is assigned dynamically by the provider.
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
