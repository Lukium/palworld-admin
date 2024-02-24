""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

from flask_socketio import SocketIO
import os
import platform
import sys
import time
from pathlib import Path

# Add the directory containing this file to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

if platform.system() == "Linux":
    sys.path.append(os.getcwd())

# fmt: off
from palworld_admin.helper.dbmigration import apply_migrations     # pylint: disable=wrong-import-position
from palworld_admin.helper.cli import parse_cli                     # pylint: disable=wrong-import-position
from palworld_admin.settings import app_settings                    # pylint: disable=wrong-import-position
from palworld_admin.website import flask_app      # pylint: disable=wrong-import-position
# fmt: on


def main():
    """Launch the Flask app and the UI app."""
    args = parse_cli()
    app_settings.set_management_mode(args["Remote"])
    app_settings.set_management_password(args["ManagementPassword"])

    if args["MigrateDatabase"]:
        apply_migrations(app_settings=app_settings)

    # Check if the user is trying to run the app on a non-Windows OS without the -r flag
    try:
        if app_settings.app_os != "Windows" and args["Remote"] != "remote":
            raise ValueError(
                "\nNon-Windows operating system requires -r and -mp flags. See -h\n"
            )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Launch the Flask app
    while not app_settings.ready:
        time.sleep(0.1)
    # apply_migrations()
    # flask_app()
    app = flask_app()
    socketio = SocketIO(app)
    socketio.run(app, host="0.0.0.0", port=8210)


# Run the app
if __name__ == "__main__":
    main()
