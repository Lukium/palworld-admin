""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

import settings as s
from website import flask_app, download_templates, download_static_files

from helper.threads import run_function_on_thread


def launch():
    """Launch the Flask app and the UI app."""
    # Start the Flask app
    run_function_on_thread(flask_app)
    # Download the remote files if necessary
    if not s.DEV_MODE:
        download_templates()
        download_static_files()
    # Start the UI app
    s.browser.open_browser()


# Run the app
if __name__ == "__main__":
    launch()
