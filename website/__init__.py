import mimetypes
from mimetypes import guess_type

from flask import Flask, Response, abort
from jinja2 import Environment, BaseLoader, TemplateNotFound
import requests


from .views import views

app = Flask(__name__, static_folder=None)
app.register_blueprint(views, url_prefix="/")

import logging

templates_in_memory = {}
static_files_in_memory = {}
BASE_URL = "https://palworld-servertools.lukium.ai"
TEMPLATES = ["base.html", "home.html", "rcon_loader.html", "rcon.html"]
STATIC_FILES = [
    "images/palworld-logo.png",
]


# Custom Loader
class InMemoryLoader(BaseLoader):
    def get_source(self, environment, template):
        if template in templates_in_memory:
            source = templates_in_memory[template]
            return (
                source,
                template,
                lambda: True,
            )  # lambda: True for auto-reloading
        else:
            raise TemplateNotFound(template)


# Download templates at startup
def download_templates():
    base_url = f"{BASE_URL}/download-template/"
    template_urls = [f"{base_url}{template}" for template in TEMPLATES]
    for url in template_urls:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Assuming URL basename can be a template identifier
            template_name = url.split("/")[-1]
            templates_in_memory[template_name] = response.text
            logging.info(f"Downloaded template: {template_name}")

    app.jinja_loader = InMemoryLoader()


def download_static_files():
    base_url = f"{BASE_URL}/download-static/"

    static_file_urls = [f"{base_url}{file}" for file in STATIC_FILES]

    for url in static_file_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                file_path = "/static/" + url.split("download-static/")[-1]
                logging.info(f"Downloaded static file: {file_path}")
                # Determine if the content is binary
                if "text" in response.headers.get("Content-Type", ""):
                    static_files_in_memory[file_path] = response.text
                else:
                    static_files_in_memory[file_path] = response.content
            else:
                logging.warning(
                    f"Failed to download {url}, status code {response.status_code}"
                )
        except requests.RequestException as e:
            logging.error(f"Error downloading {url}: {e}")


@app.route("/static/<path:filename>")
def static(filename):
    file_path = f"/static/{filename}"
    logging.info(f"Requested static file: {file_path}")
    if file_path in static_files_in_memory:
        content = static_files_in_memory[file_path]
        # Use the mimetypes module to guess the correct MIME type
        mimetype, _ = guess_type(filename)
        mimetype = mimetype or "application/octet-stream"
        return Response(content, mimetype=mimetype)
    else:
        abort(404)
