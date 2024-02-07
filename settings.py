""" This module contains the default values and descriptions for the server settings. """

import multiprocessing
import logging
import os
import platform
import sys

from classes import PalWorldSettings, LocalServer, MemoryStorage
from ui import BrowserManager

# from website import download_templates, download_static_files

WINDOWS_STEAMCMD_PATH = "steamcmd/steamcmd.exe"
LINUX_STEAMCMD_PATH = "/usr/games/steamcmd"

BASE_LAUNCHER_PATH = "steamcmd/steamapps/common/PalServer/"
WINDOWS_LAUNCHER_FILE = "PalServer.exe"
LINUX_LAUNCHER_FILE = "PalServer.sh"

PALWORLDSETTINGS_INI_BASE_PATH = f"{BASE_LAUNCHER_PATH}Pal/Saved/Config/"
PALWORLDSETTINGS_INI_FILE = "PalWorldSettings.ini"
DEFAULTPALWORLDSETTINGS_INI_FILE = "DefaultPalWorldSettings.ini"

BASE_URL = "https://palworld-servertools.lukium.ai"
TEMPLATES = [
    "base.html",
    "home.html",
    "rcon_loader.html",
    "rcon.html",
    "server_installer.html",
    "settings_gen.html",
]
STATIC_FILES = [
    "images/palworld-logo.png",
]


class Settings:
    """Class to manage the settings for the server.
    This class is used to store and manage the server settings."""

    def __init__(self):
        self.dev: bool = False
        self.app_os = ""
        self.server_os = ""
        self.main_ui = BrowserManager()

        self.palworldsettings_defaults = PalWorldSettings()
        self.localserver = LocalServer()
        self.memorystorage = MemoryStorage(BASE_URL, TEMPLATES, STATIC_FILES)

        self.pyinstaller_mode: bool = False

        self.working_server = ""

        self.set_logging()
        self.set_app_os()
        self.set_pyinstaller_mode()
        self.enable_multiprocessing_freeze_support()
        self.set_local_server_paths()
        self.download_ui()

    def set_logging(self):
        """Set the logging configuration."""
        if self.dev:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - %(levelname)s - %(message)s",
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
            )

    def set_pyinstaller_mode(self):
        """Set the pyinstaller mode based on the current environment."""
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            self.pyinstaller_mode = True
        else:
            self.pyinstaller_mode = False

    def enable_multiprocessing_freeze_support(self):
        """Enable multiprocessing.freeze_support()
        if the application is running in pyinstaller mode."""
        if self.pyinstaller_mode:
            multiprocessing.freeze_support()
            logging.info("Multiprocessing freeze support enabled.")

    def set_local_server_paths(self):
        """Set the paths for the local server based on the current environment."""
        if self.pyinstaller_mode:
            exe_path = os.path.dirname(sys.executable)
        else:
            exe_path = os.getcwd()
        windows_or_linux = "Windows" if self.app_os == "Windows" else "Linux"
        # Set the launcher path and steamcmd path based on the operating system
        if windows_or_linux == "Windows":
            self.localserver.launcher_path = os.path.join(
                exe_path, BASE_LAUNCHER_PATH, WINDOWS_LAUNCHER_FILE
            )
            self.localserver.steamcmd_path = os.path.join(
                exe_path, WINDOWS_STEAMCMD_PATH
            )
        else:
            self.localserver.launcher_path = os.path.join(
                exe_path, BASE_LAUNCHER_PATH, LINUX_LAUNCHER_FILE
            )
            self.localserver.steamcmd_path = LINUX_STEAMCMD_PATH
        # Set the default PalWorldSettings.ini path based on the operating system
        self.localserver.default_ini_path = os.path.join(
            exe_path,
            BASE_LAUNCHER_PATH,
            DEFAULTPALWORLDSETTINGS_INI_FILE,
        )
        # Set the PalWorldSettings.ini path based on the operating system
        self.localserver.ini_path = os.path.join(
            exe_path,
            PALWORLDSETTINGS_INI_BASE_PATH,
            f"{windows_or_linux}Server",
            PALWORLDSETTINGS_INI_FILE,
        )
        logging.info(
            "Local server steamcmd path: %s", self.localserver.steamcmd_path
        )
        logging.info(
            "Local server launcher path: %s", self.localserver.launcher_path
        )
        logging.info("Local server ini path: %s", self.localserver.ini_path)

    def set_app_os(self):
        """Set the operating system of the application based on the current environment."""
        result = platform.system()
        if result == "Windows":
            self.app_os = "Windows"
        elif result == "Linux":
            self.app_os = "Linux"
        elif result == "Darwin":
            self.app_os = "Mac"
        else:
            raise ValueError("Unknown operating system.")
        logging.info("Application OS: %s", self.app_os)

    def set_working_server(self, local_or_remote: str):
        """Set the working server to either local or remote."""
        self.working_server = local_or_remote
        logging.info("Working server: %s", self.working_server)

    def download_ui(self):
        """Download the UI files if necessary."""
        if not self.dev:
            self.memorystorage.download_static_files()
            self.memorystorage.download_templates()


app_settings = Settings()
