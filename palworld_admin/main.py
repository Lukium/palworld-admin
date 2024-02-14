""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

import time
import sys
from pathlib import Path

# Add the directory containing this file to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from settings import app_settings
from website import flask_app

from helper.cli import parse_cli


from helper.threads import run_function_on_thread


def main():
    """Launch the Flask app and the UI app."""
    args = parse_cli()
    app_settings.set_management_mode(args["Remote"])
    app_settings.set_management_password(args["ManagementPassword"])
    try:
        if app_settings.app_os != "Windows" and args["Remote"] != "remote":
            raise ValueError(
                "\nNon-Windows operating system requires -r and -mp flags. See -h\n"
            )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if app_settings.app_os == "Windows":
        # Start the Flask app
        run_function_on_thread(flask_app)
        # Start the UI app
        while not app_settings.ready:
            time.sleep(0.5)
        app_settings.main_ui.open_browser()

    else:
        flask_app()


# Run the app
if __name__ == "__main__":
    main()
