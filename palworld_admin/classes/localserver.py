"""This file contains the class LocalServer"""

import datetime
import subprocess


class LocalServer:
    """This class is used to store the paths of the local server."""

    def __init__(self):
        self.management_mode = ""
        self.management_password = ""
        self.steamcmd_path = ""
        self.launcher_path = ""
        self.ini_path = ""
        self.sav_path = ""
        self.default_ini_path = ""
        self.executable: str = ""
        self.pid = None
        self.socket = None
        self.palguard_installed: bool = False
        self.server_process: subprocess.Popen = None

        # RCON Variables
        self.base64_encoded: bool = False
        self.connected: bool = False
        self.launch_rcon_on_startup: bool = False
        self.rcon_monitoring_interval = 2
        self.rcon_monitoring_connection_error_count = 0
        self.ip: str = ""
        self.port: int = 0
        self.password: str = ""

        ##### Server Manager Variables #####
        self.steamcmd_installed: bool = False
        self.palserver_installed: bool = False
        self.installing: bool = False
        self.running: bool = False
        self.expected_to_be_running: bool = False
        self.first_run: bool = False
        self.shutting_down: bool = False
        self.restarting: bool = False
        self.running_check_count: int = 0
        self.server_monitoring_interval = 5

        # Backup Variables
        self.backup_path = ""
        self.data_path = ""
        self.run_auto_backup: bool = False
        self.backup_interval = 0
        self.backup_retain_count = 0
        self.last_backup: datetime.datetime = None

        # Usage Variables
        self.cpu_cores = 0
        self.use_get_counters: bool = True
        self.get_counters_succeeded: bool = False
        self.is_virtual_machine: bool = False
        self.last_cpu_check: datetime.datetime = None
        self.last_cpu_time: float = None
        self.last_cpu_usage: float = None
        self.last_ram_usage: float = None

        # Auto Restart Variables
        self.last_launcher_args: dict = {}
        self.auto_restart_monitoring: bool = False
        self.auto_restart_ram_threshold: float = 0
        self.auto_restart_on_unexpected_shutdown: bool = False
