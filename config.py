import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load variables from .env file into environment
load_dotenv()

class Config:
    """
    Central Configuration class for EduConnect.
    Supports local .env, environment variables, connection URLs, and cloud hosting.
    """
    # Secret key
    SECRET_KEY = os.getenv('SECRET_KEY') or os.getenv('secret_key') or 'educonnect-production-secret-2026'

    # Check if a single database URL was provided (e.g. DATABASE_URL or MYSQL_URL)
    db_url = os.getenv('DATABASE_URL') or os.getenv('MYSQL_URL')
    if db_url and ('mysql://' in db_url or 'mysql+mysqlconnector://' in db_url):
        # Normalize protocol if needed
        clean_url = db_url.replace('mysql+mysqlconnector://', 'mysql://')
        parsed = urlparse(clean_url)
        DB_HOST = parsed.hostname
        DB_PORT = parsed.port or 3306
        DB_USER = parsed.username
        DB_PASSWORD = parsed.password or ''
        DB_NAME = parsed.path.lstrip('/') or 'test'
    else:
        # Case-insensitive environment variable checks
        DB_HOST = (
            os.getenv('DB_HOST') or 
            os.getenv('db_host') or 
            os.getenv('MYSQL_HOST') or 
            os.getenv('mysql_host') or 
            'localhost'
        )
        DB_PORT = int(
            os.getenv('DB_PORT') or 
            os.getenv('db_port') or 
            os.getenv('MYSQL_PORT') or 
            os.getenv('mysql_port') or 
            3306
        )
        DB_USER = (
            os.getenv('DB_USER') or 
            os.getenv('db_user') or 
            os.getenv('MYSQL_USER') or 
            os.getenv('mysql_user') or 
            'root'
        )
        DB_PASSWORD = (
            os.getenv('DB_PASSWORD') or 
            os.getenv('db_password') or 
            os.getenv('MYSQL_PASSWORD') or 
            os.getenv('mysql_password') or 
            ''
        )
        DB_NAME = (
            os.getenv('DB_NAME') or 
            os.getenv('db_name') or 
            os.getenv('MYSQL_DATABASE') or 
            os.getenv('mysql_database') or 
            'educonnect_db'
        )

    # Optional AI Assistant API Key (Gemini)
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('gemini_api_key') or ''

    # Server Port & Debug Mode
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
