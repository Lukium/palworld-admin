""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

import time
import logging
import sys
from pathlib import Path

# Add the directory containing this file to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# fmt: off
from palworld_admin.settings import app_settings                    # pylint: disable=wrong-import-position
from palworld_admin.website import flask_app                        # pylint: disable=wrong-import-position
from palworld_admin.helper.cli import parse_cli                     # pylint: disable=wrong-import-position
from palworld_admin.helper.threads import run_function_on_thread    # pylint: disable=wrong-import-position
# fmt: on


def main():
    """Launch the Flask app and the UI app."""
    args = parse_cli()
    app_settings.set_management_mode(args["Remote"])
    app_settings.set_management_password(args["ManagementPassword"])

    # Check if the user is trying to run the app on a non-Windows OS without the -r flag
    try:
        if app_settings.app_os != "Windows" and args["Remote"] != "remote":
            raise ValueError(
                "\nNon-Windows operating system requires -r and -mp flags. See -h\n"
            )
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if app_settings.app_os == "Windows":
        # PyInstaller mode means the app uses the UI and Flask app
        if app_settings.pyinstaller_mode:
            logging.info("Running in PyInstaller mode")
            # Start the Flask app in a separate thread so that it can be automatically closed
            run_function_on_thread(flask_app)

            # Wait for the Flask app to start
            while not app_settings.ready:
                time.sleep(0.1)

            # app_settings.main_ui.open_browser()

            # Keep the main thread alive until the UI app is closed
            while app_settings.main_ui.poll() is None:
                time.sleep(1)

            # Close the Flask app once the UI app is closed
            logging.info(
                "Process finished with exit code %s",
                app_settings.main_ui.poll(),
            )
            exit(0)
        else:
            # Run the Flask app in the main thread
            flask_app()

    else:
        flask_app()


# Run the app
if __name__ == "__main__":
    main()
