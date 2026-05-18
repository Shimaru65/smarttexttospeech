"""WSGI entry point — used by Gunicorn (Linux) and Waitress (Windows) in production."""
from app import app

if __name__ == "__main__":
    app.run()
