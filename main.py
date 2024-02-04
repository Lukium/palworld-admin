""" This file is the entry point for the application.
It launches the Flask app and then the UI for the app. """

import logging
import threading

from waitress import serve

import settings as s
from website import app, download_templates, download_static_files


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

USE_REMOTEL_FILES = True


# Serve the Flask app with Waitress
def run_flask_app():
    """Run the Flask app with Waitress."""
    serve(app, host="0.0.0.0", port=8210)


def launch():
    """Launch the Flask app and the UI app."""
    # Run the Flask app
    flask_thread = threading.Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    s.browser.open_browser()


# Run the app
if __name__ == "__main__":
    if USE_REMOTEL_FILES:
        download_templates()
        download_static_files()
    launch()
