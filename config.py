import os
from pathlib import Path

basedir = Path(__file__).resolve().parent


class Config:
    """Base configuration for the Flask application."""

    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f"sqlite:///{basedir / 'dismissal_checker.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Babel configuration for internationalization
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'Africa/Cairo'

    # Upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
