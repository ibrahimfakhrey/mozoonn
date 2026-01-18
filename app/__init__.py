from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel

from config import Config

# SQLAlchemy instance shared across modules
db = SQLAlchemy()
babel = Babel()


def create_app(config_class: type[Config] = Config) -> Flask:
    """Application factory for the dismissal checker app."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    babel.init_app(app)

    from .routes import main_bp  # pylint: disable=import-outside-toplevel
    from .admin import init_admin  # pylint: disable=import-outside-toplevel

    app.register_blueprint(main_bp)
    
    # Initialize Flask-Admin
    init_admin(app)

    with app.app_context():
        db.create_all()
        register_cli_commands(app)

    return app


def register_cli_commands(app: Flask) -> None:
    """Register custom Flask CLI commands."""
    from .cli import register as register_cli

    register_cli(app)
