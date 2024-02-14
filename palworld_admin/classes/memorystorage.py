import logging

from jinja2 import BaseLoader, TemplateNotFound
import requests


class InMemoryTemplateLoader(BaseLoader):
    """A Jinja2 template loader that loads templates from memory."""

    def __init__(self, templates_in_memory):
        self.templates_in_memory = templates_in_memory

    def get_source(self, environment, template):
        if template in self.templates_in_memory:
            source = self.templates_in_memory[template]
            return (
                source,
                template,
                lambda: True,
            )  # lambda: True for auto-reloading
        else:
            raise TemplateNotFound(template)


class MemoryStorage:
    """This class is used to store the templates and static files in memory."""

    def __init__(self, host, templates_to_get, static_files_to_get):
        self.host = host
        self.templates_to_get = templates_to_get
        self.static_files_to_get = static_files_to_get
        self.templates_in_memory = {}
        self.static_files_in_memory = {}
        self.template_loader = InMemoryTemplateLoader(self.templates_in_memory)

    def download_templates(self):
        """Download the templates from the remote server and store them in memory."""
        base_url = f"{self.host}/download-template/"
        template_urls = [
            f"{base_url}{template}" for template in self.templates_to_get
        ]
        for url in template_urls:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                # Assuming URL basename can be a template identifier
                template_name = url.split("/")[-1]
                self.templates_in_memory[template_name] = response.text
                info = f"Downloaded template: {template_name}"
                logging.info(info)

    def download_static_files(self):
        """Download the static files from the remote server and store them in memory."""
        base_url = f"{self.host}/download-static/"

        static_file_urls = [
            f"{base_url}{file}" for file in self.static_files_to_get
        ]

        for url in static_file_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    file_path = "/static/" + url.split("download-static/")[-1]
                    info = f"Downloaded static file: {file_path}"
                    logging.info(info)
                    # Determine if the content is binary
                    if "text" in response.headers.get("Content-Type", ""):
                        self.static_files_in_memory[file_path] = response.text
                    else:
                        self.static_files_in_memory[file_path] = (
                            response.content
                        )
                else:
                    info = f"Failed to download {url}, status code {response.status_code}"
                    logging.warning(info)
            except requests.RequestException as e:
                error_message = f"Error downloading {url}: {e}"
                logging.error(error_message)
