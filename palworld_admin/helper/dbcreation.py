import os

from flask import Flask
from flask_migrate import Migrate

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
