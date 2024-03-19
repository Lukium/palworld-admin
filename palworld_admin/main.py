""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

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
from palworld_admin.settings import app_settings                    # pylint: disable=wrong-import-position
from palworld_admin.website import flask_app                        # pylint: disable=wrong-import-position
# fmt: on


def main():
    """Launch the Flask app and the UI app."""
    # Launch the Flask app once the settings are ready
    while not app_settings.settings_ready:
        time.sleep(0.1)

    app = flask_app()
    return app


# Run the app
if __name__ == "__main__":
    main()
