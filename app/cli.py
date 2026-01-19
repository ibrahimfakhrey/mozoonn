"""CLI commands for the Dismissal Checker application."""

import click
from flask import Flask


def register(app: Flask) -> None:
    """Register CLI commands with the Flask application."""

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database."""
        from . import db
        db.create_all()
        click.echo('Database initialized.')

    @app.cli.command('reset-warnings')
    def reset_warnings():
        """Reset all teacher warnings to 0."""
        from . import db
        from .models import Teacher
        count = Teacher.query.update({Teacher.warnings: 0, Teacher.late_count: 0})
        db.session.commit()
        click.echo(f'Reset warnings for {count} teachers.')
