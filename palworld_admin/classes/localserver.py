"""This file contains the class LocalServer"""

import datetime


class LocalServer:
    """This class is used to store the paths of the local server."""

    def __init__(self):
        self.last_backup: datetime.datetime = None
        self.last_cpu_check: datetime.datetime = None
        self.last_cpu_time: float = None
        self.use_get_counters: bool = True
        self.is_virtual_machine: bool = False
        self.cpu_cores = 0
        self.management_mode = ""
        self.management_password = ""
        self.steamcmd_path = ""
        self.steamcmd_installed: bool = False
        self.backup_path = ""
        self.run_auto_backup: bool = False
        self.backup_interval = 0
        self.backup_retain_count = 0
        self.data_path = ""
        self.launcher_path = ""
        self.ini_path = ""
        self.palserver_installed: bool = False
        self.default_ini_path = ""
        self.connected: bool = False
        self.running: bool = False
        self.expected_to_be_running: bool = False
        self.ip: str = ""
        self.executable: str = ""
        self.pid = None
