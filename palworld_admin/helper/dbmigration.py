"""Database migration helper functions."""

import ctypes
from ctypes import wintypes

import logging
import os
import sys
import uuid

import pkg_resources

from flask import Flask
from flask_migrate import Migrate, upgrade

from palworld_admin.classes.dbmodels import db

# from palworld_admin.settings import app_settings


def get_long_path_name(short_path):
    """
    Resolves a short path to its long form.
    """
    buffer_size = 256
    buffer = ctypes.create_unicode_buffer(buffer_size)
    long_path_name = ctypes.windll.kernel32.GetLongPathNameW
    long_path_name.argtypes = [
        wintypes.LPCWSTR,
        wintypes.LPWSTR,
        wintypes.DWORD,
    ]
    long_path_name.restype = wintypes.DWORD

    result_size = long_path_name(short_path, buffer, buffer_size)
    if result_size == 0:
        raise ctypes.WinError()

    return buffer[:result_size]


def apply_migrations(exe_path: str = None):
    """Apply any outstanding Alembic migrations."""
    app = Flask(__name__)
    app.secret_key = uuid.uuid4().hex
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f'sqlite:///{os.path.join(exe_path,"palworld-admin.db")}'
    )

    if not os.path.exists(os.path.join(exe_path, "palworld-admin.db")):
        logging.error("Database file not found.")
        sys.exit(1)

    db.init_app(app)

    migrations_directory = "migrations"  # Default migrations directory path
    migrations_directory = pkg_resources.resource_filename(
        "palworld_admin", migrations_directory
    )

    # Check if any shortening of the path took place
    if "~" in migrations_directory:
        migrations_directory = get_long_path_name(migrations_directory)

    try:
        logging.info("Applying Database Migrations if any...")
        with app.app_context():
            Migrate(app, db)
            upgrade(directory=migrations_directory)
        sys.exit(0)
    except Exception as e:  # pylint: disable=broad-except
        logging.error("Error applying migrations: %s", e)
        sys.exit(1)
