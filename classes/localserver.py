"""This file contains the class LocalServer"""


class LocalServer:
    """This class is used to store the paths of the local server."""

    def __init__(self):
        self.management_mode = ""
        self.management_password = ""
        self.authenticated: bool = False
        self.steamcmd_path = ""
        self.steamcmd_installed: bool = False
        self.backup_path = ""
        self.data_path = ""
        self.launcher_path = ""
        self.ini_path = ""
        self.palserver_installed: bool = False
        self.default_ini_path = ""
        self.connected: bool = False
        self.running: bool = False
        self.ip: str = ""
