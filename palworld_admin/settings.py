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
from palworld_admin.helper.cli import parse_cli
from palworld_admin.helper.consolemanagement import (
    hide_console,
)  # pylint: disable=wrong-import-position
from palworld_admin.helper.oscommands import detect_virtual_machine
from palworld_admin.helper.dbmigration import apply_migrations

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
DEV_TEMPLATES = [
    "ui-test.html",
    "login.html",
]
SUPPORTER_TEMPLATES = [
    "ui-supporter.html",
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
        self.dev_ui: bool = False
        self.no_ui: bool = True
        self.version: str = "0.9.9"
        self.supporter_build: bool = False
        self.supporter_version: str = "0.9.9"
        self.migration_mode: bool = False
        self.alembic_version: str = "59a004fd30a9"
        self.exe_path: str = ""
        self.app_os = ""
        self.app_port: int = 8210
        self.main_ui = None
        self.ready = False
        self.force_error = False
        self.meipass = None
        self.steam_openid_url = "https://steamcommunity.com/openid"

        self.cli_launch_server: bool = False
        self.cli_management_password: str = ""
        self.cli_migrate_database: bool = False
        self.cli_no_console: bool = False
        self.cli_no_ui: bool = False
        self.cli_port: int = 8210
        self.cli_remote: bool = False

        self.palworldsettings_defaults = PalWorldSettings()
        self.localserver = LocalServer()
        self.memorystorage = MemoryStorage(
            BASE_URL,
            (
                DEV_TEMPLATES
                if self.dev_ui
                else SUPPORTER_TEMPLATES if self.supporter_build else TEMPLATES
            ),
            STATIC_FILES,
        )

        self.pyinstaller_mode: bool = False

        # self.shutdown_requested = False

        self.current_client: str = None

        self.set_logging()
        # self.set_pyinstaller_mode()
        self.set_app_os()
        self.detect_virtual_machine()
        self.detect_cpu_cores()
        self.set_local_server_paths()
        self._parse_cli()
        self.check_for_palguard()
        self.download_ui()
        self.launch_ui()
        self.monitor_shutdown()
        self.settings_ready = True
        self.app_ready = False

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

    # def set_pyinstaller_mode(self):
    #     """Set the pyinstaller mode based on the current environment."""
    #     if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    #         self.pyinstaller_mode = True
    #         self.meipass = sys._MEIPASS  # pylint: disable=protected-access
    #         logging.info("MEIPASS: %s", self.meipass)
    #     else:
    #         self.pyinstaller_mode = False
    #     logging.info("Pyinstaller mode: %s", self.pyinstaller_mode)

    def set_local_server_paths(self):
        """Set the paths for the local server based on the current environment."""
        # if self.pyinstaller_mode:
        #     exe_path = os.path.dirname(sys.executable)
        # else:
        exe_path = os.getcwd()
        self.exe_path = exe_path
        windows_or_linux = (
            "Windows"
            if self.app_os == "Windows" or self.app_os == "Wine"
            else "Linux"
        )
        # Set the launcher path and steamcmd path based on the operating system
        if self.app_os == "Windows":
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

        elif self.app_os == "Linux":
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

        elif self.app_os == "Wine":
            wineprefix = os.environ["WINEPREFIX"]
            base_launcher_path = os.path.join(
                wineprefix,
                "drive_c",
                WINDOWS_BASE_LAUNCHER_PATH,
            )

            self.localserver.launcher_path = os.path.join(
                "wine",
                base_launcher_path,
                WINDOWS_LAUNCHER_FILE,
            )

            self.localserver.steamcmd_path = os.path.join(
                wineprefix,
                "drive_c",
                WINDOWS_STEAMCMD_PATH,
            )

            self.localserver.default_ini_path = os.path.join(
                wineprefix,
                "drive_c",
                base_launcher_path,
                DEFAULTPALWORLDSETTINGS_INI_FILE,
            )

            self.localserver.ini_path = os.path.join(
                wineprefix,
                "drive_c",
                base_launcher_path,
                PALWORLDSETTINGS_INI_BASE_PATH,
                f"{windows_or_linux}Server",
                PALWORLDSETTINGS_INI_FILE,
            )

            self.localserver.data_path = os.path.join(
                wineprefix,
                "drive_c",
                base_launcher_path,
                LOCAL_SERVER_DATA_PATH,
            )

            self.localserver.executable = WINDOWS_SERVER_EXECUTABLE

        self.localserver.backup_path = os.path.join(
            exe_path, LOCAL_SERVER_BACKUP_PATH
        )

        if windows_or_linux == "Linux":
            bin_dir = "Linux"
        else:
            bin_dir = "Win64"

        self.localserver.binaries_path = os.path.join(
            base_launcher_path,
            "Pal",
            "Binaries",
            bin_dir,
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

        logging.info(
            "Local server binaries path: %s", self.localserver.binaries_path
        )

    def set_app_os(self):
        """Set the operating system of the application based on the current environment."""
        # Check if the app is running in Wine by checking the WINEPREFIX environment variable
        env = os.environ
        if "WINEPREFIX" in env:
            self.app_os = "Wine"
            logging.info("Application OS: %s", self.app_os)
            # Export WINEDEBUG=-all to disable all Wine debugging
            env["WINEDEBUG"] = "-all"
            return
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
        if self.migration_mode:
            return
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

    def check_for_palguard(self):
        """Check if PalGuard is installed."""
        if self.app_os == "Windows":
            palguard_path = os.path.join(
                self.exe_path,
                WINDOWS_BASE_LAUNCHER_PATH,
                "Pal",
                "Binaries",
                "Win64",
                "palguard.dll",
            )
            if os.path.exists(palguard_path):
                self.localserver.palguard_installed = True
                logging.info(
                    "PalGuard installed: %s",
                    self.localserver.palguard_installed,
                )

    def detect_cpu_cores(self):
        """Detect the number of CPU cores."""
        self.localserver.cpu_cores = multiprocessing.cpu_count()
        logging.info("CPU cores: %s", self.localserver.cpu_cores)

    def _parse_cli(self):
        """Parse CLI arguments."""
        args = parse_cli()

        self.cli_launch_server = args["LaunchServer"]
        self.cli_port = args["Port"]
        self.cli_no_ui = args["NoUserInterface"]
        self.cli_no_console = args["NoConsole"]
        self.cli_migrate_database = args["MigrateDatabase"]
        self.cli_remote = args["Remote"]
        self.cli_management_password = args["ManagementPassword"]

        self.app_port = args["Port"]
        self.set_management_mode(self.cli_remote)
        self.set_management_password(self.cli_management_password)

        try:
            if self.app_os != "Windows" and self.cli_remote != "remote":
                raise ValueError(
                    "\nNon-Windows operating system requires -r and -mp flags. See -h\n"
                )
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

        if self.cli_migrate_database:
            self.migration_mode = True
            apply_migrations(self.exe_path)
            sys.exit(0)

        if self.cli_no_console:
            hide_console()

    def launch_ui(self):
        """Launch the main UI."""
        # If the app is being built for pip, then don't launch the UI
        if self.migration_mode or self.cli_no_ui or self.no_ui:
            return
        if self.app_os == "Windows":
            try:
                # if self.pyinstaller_mode:
                #     ui_path = os.path.join(
                #         self.meipass,
                #         "ui",
                #         "palworld-admin-ui.exe",
                #     )
                # else:
                ui_path = os.path.join(
                    self.exe_path,
                    "ui",
                    "palworld-admin-ui-win32-x64",
                    "palworld-admin-ui.exe",
                )

                if not os.path.exists(ui_path):
                    logging.info("UI not found, skipping launch.")
                else:
                    logging.info("Launching UI: %s", ui_path)
                    self.main_ui = subprocess.Popen(
                        [ui_path, f"--port={str(self.app_port)}"]
                    )
                    logging.info("Launched UI.")
            except Exception as e:  # pylint: disable=broad-except
                logging.error("Failed to launch UI: %s", e)
                sys.exit(1)
        else:  # Linux
            pass  # No UI for Linux

    def monitor_shutdown(self):
        """Monitor the shutdown status of the UI."""
        if self.main_ui is None:
            return

        def monitor():
            # while not self.shutdown_requested:
            #     time.sleep(1)
            # Check if the UI is still running using poll
            while True:
                if self.main_ui.poll() is not None:
                    logging.info("UI has closed.")
                    break
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


app_settings = Settings()
