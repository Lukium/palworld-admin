""" Database models for the application. """

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class AlembicVersion(db.Model):
    """Alembic version model for the application."""

    version_num = db.Column(db.String(32), primary_key=True)


class Settings(db.Model):
    """Settings model for the application."""

    id = db.Column(db.Integer, primary_key=True)
    launcher_settings_id = db.Column(
        db.Integer, db.ForeignKey("launcher_settings.id"), nullable=False
    )
    rcon_settings_id = db.Column(
        db.Integer, db.ForeignKey("rcon_settings.id"), nullable=False
    )
    launcher_settings = relationship(
        "LauncherSettings", backref="settings", uselist=False
    )
    rcon_settings = relationship(
        "RconSettings", backref="settings", uselist=False
    )


class LauncherSettings(db.Model):
    """Launcher settings model for the application."""

    id = db.Column(db.Integer, primary_key=True)
    launch_rcon = db.Column(db.Boolean, default=True)
    steam_auth = db.Column(db.Boolean, default=False)
    enforce_steam_auth_ip = db.Column(db.Boolean, default=False)
    useperfthreads = db.Column(db.Boolean, default=True)
    NoAsyncLoadingThread = db.Column(db.Boolean, default=True)
    UseMultithreadForDS = db.Column(db.Boolean, default=True)
    query_port = db.Column(db.Integer, default=27015)
    auto_backup = db.Column(db.Boolean, default=True)
    auto_backup_delay = db.Column(db.Integer, default=3600)
    auto_backup_quantity = db.Column(db.Integer, default=48)
    publiclobby = db.Column(db.Boolean, default=False)
    auto_restart_triggers = db.Column(db.Boolean, default=True)
    auto_restart_on_unexpected_shutdown = db.Column(db.Boolean, default=True)
    ram_restart_trigger = db.Column(db.Float, default=0.0)


class RconSettings(db.Model):
    """Rcon settings model for the application."""

    id = db.Column(db.Integer, primary_key=True)
    connection_id = db.Column(
        db.Integer, db.ForeignKey("connection.id"), nullable=False
    )
    connection = relationship(
        "Connection", backref="rcon_settings", uselist=False
    )


class Connection(db.Model):
    """Connection model for the application."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    host = db.Column(db.String(255))
    port = db.Column(db.Integer)
    password = db.Column(db.String(255))


class Players(db.Model):
    """Players model for the application."""

    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(255), unique=True)
    steam_authenticated = db.Column(db.Boolean, default=False)
    steam_auth_ip = db.Column(db.String(255))
    online = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(255))
    player_id = db.Column(db.String(255))
    save_id = db.Column(db.String(255))
    first_login = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
    whitelisted = db.Column(db.Boolean, default=False)
    whitelisted_ip = db.Column(db.String(255))
    banned = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
