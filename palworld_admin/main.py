""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from flask_socketio import SocketIO

# Add the directory containing this file to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

if platform.system() == "Linux":
    sys.path.append(os.getcwd())

# fmt: off
from palworld_admin.helper.consolemanagement import hide_console    # pylint: disable=wrong-import-position
from palworld_admin.helper.dbmigration import apply_migrations      # pylint: disable=wrong-import-position
from palworld_admin.helper.cli import parse_cli                     # pylint: disable=wrong-import-position
from palworld_admin.settings import app_settings                    # pylint: disable=wrong-import-position
from palworld_admin.website import flask_app                        # pylint: disable=wrong-import-position
# fmt: on


def main():
    """Launch the Flask app and the UI app."""
    args = parse_cli()
    app_settings.set_management_mode(args["Remote"])
    app_settings.set_management_password(args["ManagementPassword"])

    if args["MigrateDatabase"]:
        # Terminate the UI if only the database migration is required
        while not app_settings.ready:
            time.sleep(0.1)
        ui: subprocess.Popen = app_settings.main_ui
        if ui:
            ui.terminate()
        apply_migrations()

    if args["NoUserInterface"]:
        # Terminate the UI if the user interface is not required
        while not app_settings.ready:
            time.sleep(0.1)
        ui: subprocess.Popen = app_settings.main_ui
        if ui:
            ui.terminate()
            logging.info(
                "User interface closed since launched with --no-user-interface."
            )

    if args["NoConsole"]:
        hide_console()

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

    app = flask_app()
    return app


# Run the app
if __name__ == "__main__":
    socketio = SocketIO(main())
    socketio.run(main(), host="0.0.0.0", port=8210)
