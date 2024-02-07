""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

# import settings as s
from settings import app_settings
from website import flask_app

from helper.threads import run_function_on_thread


def launch():
    """Launch the Flask app and the UI app."""
    # Start the Flask app
    run_function_on_thread(flask_app)
    # Start the UI app
    app_settings.main_ui.open_browser()


# Run the app
if __name__ == "__main__":
    launch()
