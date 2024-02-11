""" This module contains the default values and descriptions for the server settings. """

import logging
import multiprocessing
import os
import platform
import sys

from classes import PalWorldSettings, LocalServer, MemoryStorage
from ui import BrowserManager

# from website import download_templates, download_static_files

WINDOWS_STEAMCMD_PATH = "steamcmd/steamcmd.exe"
LINUX_STEAMCMD_PATH = "/usr/games/steamcmd"

WINDOWS_BASE_LAUNCHER_PATH = "steamcmd/steamapps/common/PalServer/"
LINUX_BASE_LAUNCHER_PATH = ".steam/steam/steamapps/common/PalServer/"


WINDOWS_LAUNCHER_FILE = "PalServer.exe"
LINUX_LAUNCHER_FILE = "PalServer.sh"

PALWORLDSETTINGS_INI_BASE_PATH = "Pal/Saved/Config/"
PALWORLDSETTINGS_INI_FILE = "PalWorldSettings.ini"
DEFAULTPALWORLDSETTINGS_INI_FILE = "DefaultPalWorldSettings.ini"

LOCAL_SERVER_BACKUP_PATH = "Backups/"
LOCAL_SERVER_DATA_PATH = "Pal/Saved"

BASE_URL = "https://palworld-servertools.lukium.ai"
TEMPLATES = [
    "home.html",
    "login.html",
    "main.html",
    "rcon.html",
    "server_installer.html",
    "settings_gen.html",
]
STATIC_FILES = [
    "images/palworld-logo.png",
    "images/icon.png",
]


class Settings:
    """Class to manage the settings for the server.
    This class is used to store and manage the server settings."""

    def __init__(self):
        self.dev: bool = False
        self.version: str = "0.6.2"
        self.app_os = ""
        self.server_os = ""
        self.main_ui = BrowserManager()

        self.palworldsettings_defaults = PalWorldSettings()
        self.localserver = LocalServer()
        self.memorystorage = MemoryStorage(BASE_URL, TEMPLATES, STATIC_FILES)

        self.pyinstaller_mode: bool = False

        self.set_logging()
        self.set_pyinstaller_mode()
        self.set_app_os()
        self.detect_cpu_cores()
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

    def set_local_server_paths(self):
        """Set the paths for the local server based on the current environment."""
        if self.pyinstaller_mode:
            exe_path = os.path.dirname(sys.executable)
        else:
            exe_path = os.getcwd()
        windows_or_linux = "Windows" if self.app_os == "Windows" else "Linux"
        # Set the launcher path and steamcmd path based on the operating system
        if windows_or_linux == "Windows":
            # Set the base launcher path based on the operating system
            base_launcher_path = WINDOWS_BASE_LAUNCHER_PATH

            # Set the launcher path based on the operating system
            self.localserver.launcher_path = os.path.join(
                exe_path, base_launcher_path, WINDOWS_LAUNCHER_FILE
            )

            # Set the steamcmd path based on the operating system
            self.localserver.steamcmd_path = os.path.join(
                exe_path, WINDOWS_STEAMCMD_PATH
            )

            # Set the default PalWorldSettings.ini path based on the operating system
            self.localserver.default_ini_path = os.path.join(
                exe_path,
                base_launcher_path,
                DEFAULTPALWORLDSETTINGS_INI_FILE,
            )

            # Set the PalWorldSettings.ini path based on the operating system
            self.localserver.ini_path = os.path.join(
                exe_path,
                base_launcher_path,
                PALWORLDSETTINGS_INI_BASE_PATH,
                f"{windows_or_linux}Server",
                PALWORLDSETTINGS_INI_FILE,
            )

            # Set the backup path based on the operating system
            self.localserver.data_path = os.path.join(
                exe_path,
                base_launcher_path,
                LOCAL_SERVER_DATA_PATH,
            )

        else:
            home_dir = os.environ["HOME"]
            base_launcher_path = os.path.join(
                home_dir, LINUX_BASE_LAUNCHER_PATH
            )

            # Set the launcher path based on the operating system
            self.localserver.launcher_path = os.path.join(
                base_launcher_path, LINUX_LAUNCHER_FILE
            )

            # Set the steamcmd path based on the operating system
            self.localserver.steamcmd_path = LINUX_STEAMCMD_PATH

            # Set the default PalWorldSettings.ini path based on the operating system
            self.localserver.default_ini_path = os.path.join(
                base_launcher_path,
                DEFAULTPALWORLDSETTINGS_INI_FILE,
            )

            # Set the PalWorldSettings.ini path based on the operating system
            self.localserver.ini_path = os.path.join(
                base_launcher_path,
                PALWORLDSETTINGS_INI_BASE_PATH,
                f"{windows_or_linux}Server",
                PALWORLDSETTINGS_INI_FILE,
            )

            # Set the backup path based on the operating system
            self.localserver.data_path = os.path.join(
                base_launcher_path,
                LOCAL_SERVER_DATA_PATH,
            )

        self.localserver.backup_path = os.path.join(
            exe_path, LOCAL_SERVER_BACKUP_PATH
        )

        logging.info(
            "Local server steamcmd path: %s", self.localserver.steamcmd_path
        )
        logging.info(
            "Local server launcher path: %s", self.localserver.launcher_path
        )
        logging.info("Local server ini path: %s", self.localserver.ini_path)
        logging.info(
            "Local server backup path: %s", self.localserver.backup_path
        )
        logging.info("Local server data path: %s", self.localserver.data_path)

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

    def set_management_mode(self, local_or_remote: str):
        """Set the working server to either local or remote."""
        self.localserver.management_mode = local_or_remote
        logging.info("Management: %s", self.localserver.management_mode)

    def set_management_password(self, password: str):
        """Set the management password for the local server."""
        self.localserver.management_password = password
        logging.info(
            "Management password: %s", self.localserver.management_password
        )

    def download_ui(self):
        """Download the UI files if necessary."""
        if not self.dev:
            self.memorystorage.download_static_files()
            self.memorystorage.download_templates()

    def detect_cpu_cores(self):
        """Detect the number of CPU cores."""
        self.localserver.cpu_cores = multiprocessing.cpu_count()
        logging.info("CPU cores: %s", self.localserver.cpu_cores)


app_settings = Settings()
