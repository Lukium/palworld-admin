""" This module contains the default values and descriptions for the server settings. """

import logging
import multiprocessing
import os
import platform
import subprocess
import sys
import time

from threading import Thread

# from palworld_admin.helper.cli import parse_cli
from palworld_admin.classes import PalWorldSettings, LocalServer, MemoryStorage
from palworld_admin.helper.oscommands import detect_virtual_machine

# from palworld_admin.ui import BrowserManager

# Get the waitress logger
logger = logging.getLogger("waitress")
logger.setLevel(logging.ERROR)  # Only show errors and above

WINDOWS_STEAMCMD_PATH = "steamcmd/steamcmd.exe"
LINUX_STEAMCMD_PATH = "/usr/games/steamcmd"

WINDOWS_BASE_LAUNCHER_PATH = "steamcmd/steamapps/common/PalServer/"
LINUX_BASE_LAUNCHER_PATH = ".steam/steam/steamapps/common/PalServer/"


WINDOWS_LAUNCHER_FILE = "PalServer.exe"
LINUX_LAUNCHER_FILE = "PalServer.sh"

WINDOWS_SERVER_EXECUTABLE = "PalServer-Win64-Test-Cmd"
LINUX_SERVER_EXECUTABLE = "PalServer-Linux-Test"

PALWORLDSETTINGS_INI_BASE_PATH = "Pal/Saved/Config/"
PALWORLDSETTINGS_INI_FILE = "PalWorldSettings.ini"
DEFAULTPALWORLDSETTINGS_INI_FILE = "DefaultPalWorldSettings.ini"

LOCAL_SERVER_BACKUP_PATH = "Backups/"
LOCAL_SERVER_DATA_PATH = "Pal/Saved"

BASE_URL = "https://palworld-servertools.lukium.ai"
TEMPLATES = [
    "ui.html",
    "login.html",
]
STATIC_FILES = [
    # "images/palworld-logo.png",
    # "images/icon.png",
]


class Settings:
    """Class to manage the settings for the server.
    This class is used to store and manage the server settings."""

    def __init__(self):
        self.dev: bool = False
        self.no_ui: bool = True
        self.version: str = "0.8.2"
        self.exe_path: str = ""
        self.app_os = ""
        self.server_os = ""
        # self.main_ui = BrowserManager()
        self.main_ui = None
        self.ready = False
        self.force_error = False
        self.meipass = None

        self.palworldsettings_defaults = PalWorldSettings()
        self.localserver = LocalServer()
        self.memorystorage = MemoryStorage(BASE_URL, TEMPLATES, STATIC_FILES)

        self.pyinstaller_mode: bool = False

        self.shutdown_requested = False

        self.current_client: str = ""

        self.set_logging()
        self.set_pyinstaller_mode()
        self.set_app_os()
        self.detect_virtual_machine()
        self.detect_cpu_cores()
        self.set_local_server_paths()
        self.download_ui()
        self.launch_ui()
        self.monitor_shutdown()
        self.ready = True

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
            self.meipass = sys._MEIPASS  # pylint: disable=protected-access
            logging.info("MEIPASS: %s", self.meipass)
        else:
            self.pyinstaller_mode = False
        logging.info("Pyinstaller mode: %s", self.pyinstaller_mode)

    def set_local_server_paths(self):
        """Set the paths for the local server based on the current environment."""
        if self.pyinstaller_mode:
            exe_path = os.path.dirname(sys.executable)
        else:
            exe_path = os.getcwd()
        self.exe_path = exe_path
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

            self.localserver.executable = WINDOWS_SERVER_EXECUTABLE

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
            # self.localserver.steamcmd_path = LINUX_STEAMCMD_PATH
            self.localserver.steamcmd_path = os.path.join(
                home_dir, ".local/share/Steam/steamcmd/steamcmd.sh"
            )

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

            self.localserver.executable = LINUX_SERVER_EXECUTABLE

        self.localserver.backup_path = os.path.join(
            exe_path, LOCAL_SERVER_BACKUP_PATH
        )

        # sav_path
        partial_sav_path = os.path.join(
            self.localserver.data_path, "SaveGames", "0"
        )
        # Get the first folder in the partial_sav_path if partial_sav_path exists
        if os.path.exists(partial_sav_path):
            logging.info("Partial sav path exists, using first folder.")
            self.localserver.sav_path = os.path.join(
                partial_sav_path, os.listdir(partial_sav_path)[0]
            )
        else:
            # Try to use GameUserSettings.ini to get the sav path
            target_file = os.path.join(
                base_launcher_path,
                PALWORLDSETTINGS_INI_BASE_PATH,
                f"{windows_or_linux}Server",
                "GameUserSettings.ini",
            )
            # Read DedicatedServerName value from GameUserSettings.ini if it exists
            if os.path.exists(target_file):
                logging.info(
                    "GameUserSettings.ini exists, reading DedicatedServerName."
                )
                with open(target_file, "r", encoding="utf-8") as file:
                    lines = file.readlines()
                    for line in lines:
                        if "DedicatedServerName=" in line:
                            self.localserver.sav_path = os.path.join(
                                self.localserver.data_path,
                                "SaveGames",
                                "0",
                                line.split("=")[1].strip(),
                            )
                            break

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

        logging.info("Local server sav path: %s", self.localserver.sav_path)

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

    def detect_virtual_machine(self):
        """Detect if the server is running in a virtual machine."""
        detection = detect_virtual_machine(self.app_os)
        if detection["status"] == "success":
            self.localserver.is_virtual_machine = detection["value"]
        logging.info(
            "Virtual Machine: %s", self.localserver.is_virtual_machine
        )

    def detect_cpu_cores(self):
        """Detect the number of CPU cores."""
        self.localserver.cpu_cores = multiprocessing.cpu_count()
        logging.info("CPU cores: %s", self.localserver.cpu_cores)

    def launch_ui(self):
        """Launch the main UI."""
        # If the app is being built for pip, then don't launch the UI
        if self.no_ui:
            return
        if self.app_os == "Windows":
            try:
                if self.pyinstaller_mode:
                    ui_path = os.path.join(
                        self.meipass,
                        "ui",
                        "palworld-admin-ui.exe",
                    )
                else:
                    ui_path = os.path.join(
                        self.exe_path,
                        "ui",
                        "palworld-admin-ui-win32-x64",
                        "palworld-admin-ui.exe",
                    )

                logging.info("Launching UI: %s", ui_path)
                self.main_ui = subprocess.Popen(ui_path)
                logging.info("Launched UI.")
            except Exception as e:  # pylint: disable=broad-except
                logging.error("Failed to launch UI: %s", e)
                sys.exit(1)
        else:  # Linux
            pass  # No UI for Linux

    def monitor_shutdown(self):
        """Monitor the shutdown status of the UI."""

        def monitor():
            while not self.shutdown_requested:
                time.sleep(1)
            logging.info("Shutdown requested, waiting 1 second.")
            time.sleep(1)  # Wait for the UI to close
            # Get PID of own process
            pid = os.getpid()
            logging.info("Terminating own Process with Pid: %s", pid)
            if app_settings.app_os == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True,
                    check=True,
                    startupinfo=startupinfo,
                    text=True,
                )
                # os.system(f"taskkill /F /PID {pid}")
            else:
                os.system(f"kill -9 {pid}")

        Thread(target=monitor, daemon=True).start()

    # def review_cli(self):
    #     """Parse command line arguments."""
    #     try:
    #         parsed_args = parse_cli()
    #         if parsed_args["MigrateDatabase"]:
    #             self.no_ui = True

    #         return parsed_args
    #     except ValueError as e:
    #         print(f"Error: {e}")
    #         # Optionally, you can also provide guidance or next steps:
    #         print("Use -h for help.")
    #         # Exiting with a non-zero status code to indicate that an error occurred
    #         exit(1)


app_settings = Settings()
