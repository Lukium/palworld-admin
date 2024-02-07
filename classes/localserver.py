"""This file contains the class LocalServer"""


class LocalServer:
    """This class is used to store the paths of the local server."""

    def __init__(self):
        self.steamcmd_path = ""
        self.launcher_path = ""
        self.ini_path = ""
        self.default_ini_path = ""
        self.connected: bool = False
        self.ip: str = ""
