"""Database migration helper functions."""

import logging
import os
import pkg_resources
import sys
import uuid

from flask import Flask
from flask_migrate import Migrate, upgrade

from palworld_admin.classes.dbmodels import db
from palworld_admin.settings import Settings


def apply_migrations(app_settings: Settings):
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
