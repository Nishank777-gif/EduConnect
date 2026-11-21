"""
WSGI Entry point for Cloud Deployment (Render, Railway, Heroku)
"""
from app import app

if __name__ == "__main__":
    app.run()
