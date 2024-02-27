"""Database migration helper functions."""

import logging
import os
import sys
import uuid

import pkg_resources

from flask import Flask
from flask_migrate import Migrate, upgrade

from palworld_admin.classes.dbmodels import db
from palworld_admin.settings import app_settings


def create_app():
    """Create a Flask app with the database URI set."""
    app = Flask(__name__)
    # Example configuration, adjust as necessary
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f'sqlite:///{os.path.join(app_settings.exe_path,"palworld-admin.db")}'
    )
    db.init_app(app)
    Migrate(app, db)
    return app


def apply_migrations():
    """Apply any outstanding Alembic migrations."""
    app = Flask(__name__)
    app.secret_key = uuid.uuid4().hex
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f'sqlite:///{os.path.join(app_settings.exe_path,"palworld-admin.db")}'
    )

    db.init_app(app)

    migrations_directory = "migrations"  # Default migrations directory path
    if app_settings.pyinstaller_mode:
        migrations_directory = os.path.join(
            app_settings.meipass, migrations_directory
        )
    else:
        migrations_directory = pkg_resources.resource_filename(
            "palworld_admin", migrations_directory
        )

    try:
        logging.info("Applying Database Migrations if any...")
        with app.app_context():
            Migrate(app, db)
            upgrade(directory=migrations_directory)
        sys.exit(0)
    except Exception as e:  # pylint: disable=broad-except
        logging.error("Error applying migrations: %s", e)
        sys.exit(1)
