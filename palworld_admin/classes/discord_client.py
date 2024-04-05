"""Discord client for sending messages to a specific channel in a specific server."""

import asyncio
import base64
import platform
import re
import socket
import struct
import sys
import threading
import logging

from queue import Queue

import discord
from discord import app_commands
from discord.ext import commands


class DiscordClient(commands.Bot):
    """Discord client for sending messages to a specific channel in a specific server."""

    def __init__(self, *args, **kwargs):
        """Initialize the Discord client."""
        token = kwargs.pop("token", None)
        if token is None:
            raise ValueError("Token is required")
        server_id = kwargs.pop("server_id", None)
        if server_id is None:
            raise ValueError("Server ID is required")
        channel_id = kwargs.pop("channel_id", None)
        if channel_id is None:
            raise ValueError("Channel ID is required")
        rcon_role_id = kwargs.pop("rcon_role_id", None)
        if rcon_role_id is None:
            raise ValueError("RCON Role ID is required")
        admin_role_id = kwargs.pop("admin_role_id", None)
        if admin_role_id is None:
            raise ValueError("Admin Role ID is required")
        self.token = token
        self.connected = False
        self.server_id = server_id
        self.guild = discord.Object(id=self.server_id)

        self.channel_id = channel_id
        self.channel = None

        self.rcon_role_id = rcon_role_id
        self.rcon_role = discord.Object(id=self.rcon_role_id)

        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        self.rcon_ip: str = ""
        self.rcon_port: int = 0
        self.rcon_password: str = ""
        self.base64_rcon: bool = False

        self.palguard_installed: bool = False

        self.player_count: int = 0

        super().__init__(
            command_prefix="!",  # Change to your preferred prefix
            intents=intents,
            tree_cls=app_commands.CommandTree,  # This is necessary for app_commands
        )

        self.message_queue = asyncio.Queue()

    async def setup_hook(self):
        # Retrieve the actual guild object using the guild ID.
        guild = await self.fetch_guild(self.server_id)

        if guild is None:
            logging.error("Guild with ID %s not found.", self.server_id)
            return

        logging.info("Setup Hook Guild: %s", guild)

        # Now that we have the actual guild object, we can clear commands, add commands, and sync.
        # await self.tree.clear_commands(guild=discord.Object(id=self.server_id))

        # Assuming `rcon_command` is properly defined elsewhere in your class.
        self.tree.add_command(self.rcon_command, guild=guild)

        await self.tree.sync(guild=guild)

        # Continue setting up your background tasks or other setup actions.
        self.loop.create_task(self.send_message_task())
        self.loop.create_task(self.update_presence())

    async def process_message_queue(self):
        """Process the message queue."""
        while True:
            message = await self.message_queue.get()
            logging.info("Processing message: %s", message)
            try:
                await self.send_message(message)
            except Exception as e:  # pylint: disable=broad-except
                logging.error("Error: %s", str(e))
            await asyncio.sleep(0.5)

    async def update_presence(self):
        """Update the bot's presence based on the player count."""
        await self.wait_until_ready()
        while not self.is_closed():
            await self.change_presence(
                activity=discord.Game(
                    name=f"{'alone' if self.player_count == 0 else 'with: '}{self.player_count if self.player_count > 0 else ''}{' players' if self.player_count > 1 else ' player' if self.player_count == 1 else ''}"
                )
            )
            await asyncio.sleep(60)

    async def send_message_task(self):
        """Send messages from the message queue."""
        await self.wait_until_ready()
        await self.process_message_queue()

    async def send_message(self, message: str) -> None:
        """Send a message to a specific channel in a specific server."""
        if not self.connected:
            return
        logging.info("Sending message: %s", message)
        if not message:
            logging.info("Error: Empty user_message")
            return

        if not self.channel:
            logging.error("Error: Channel not found")
            return

        try:
            await self.channel.send(message)
        except Exception as e:  # pylint: disable=broad-except
            logging.error("Error: %s", str(e))

    @app_commands.command(
        name="rcon",
        description="Send RCON Command to Dedicated Server via Palworld Admin",
    )
    async def rcon_command(
        self,
        interaction: discord.Interaction,
        *,
        command: str,
        message: str = None,
    ):
        """Send an RCON command to a dedicated server via Palworld Admin."""
        # Check if the user has the RCON_ROLE_ID
        if self.rcon_role in interaction.user.roles:
            await interaction.response.defer()
            reply = f"Sending RCON command: {command}"
            self.rcon_broadcast(message, command)
            await self.send_message(reply)
            await interaction.followup.send("RCON command sent successfully.")
        else:
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True,
            )

    async def on_ready(self) -> None:
        """Log in as the client."""
        logging.info("Logged in as %s", self.user)

        # Check if bot has access to server with SERVER_ID
        guild = discord.utils.find(
            lambda g: g.id == self.server_id, self.guilds
        )
        if not guild:
            logging.error(
                "Error: Bot does not have access to server with server id %s",
                self.server_id,
            )
            return
        else:
            logging.info("Discord Bot connected to server %s", guild)

        self.channel = self.get_channel(self.channel_id)
        if not self.channel:
            logging.error(
                "Error: Bot does not have access to channel with channel id %s",
                self.channel_id,
            )
            return
        else:
            logging.info("Discord Bot connected to channel %s", self.channel)

        logging.info(
            "Attempting to send message to Discord channel: %s", self.channel
        )
        self.connected = True
        await self.send_message("Palworld Admin is online.")

    async def start(self) -> None:
        """Start the Discord client."""
        await self.login(self.token)
        await self.connect()
        await self.wait_until_ready()

    async def shutdown(self) -> None:
        """Shutdown the Discord client."""
        await self.close()

    async def execute_rcon(self, command, queue) -> None:
        """Execute the specified RCON command and put the result in the queue."""
        log = False
        if log:
            logging.info("Executing RCON command: %s", command)
        if log:
            logging.info("Using cached IP: %s")
        host_port = f"{self.rcon_ip}:{self.rcon_port}"
        result = execute(
            host_port,
            self.rcon_password,
            command,
            base64_encoded=self.base64_rcon,
        ).strip()
        if log:
            logging.info("Command Output: %s\n", result)
        if result:
            queue.put(result.strip())

    def rcon_broadcast(self, message: str, command: str) -> dict:
        """Broadcast the specified message to the server."""
        result_queue = Queue()

        if command == "broadcast" and self.palguard_installed:
            rcon_command = "pgbroadcast"
        elif command == "custom":
            rcon_command = message.split(" ")[0]
            message = " ".join(message.split(" ")[1:])
        else:
            rcon_command = command

        command_thread = threading.Thread(
            target=self.execute_rcon,
            args=(
                self.rcon_ip,
                self.rcon_port,
                self.rcon_password,
                f"{rcon_command} {message}",
                result_queue,
            ),
        )
        command_thread.start()
        command_thread.join()  # Wait for the thread to complete

        # Retrieve the result from the queue
        result = result_queue.get()
        logging.info("Broadcast Result: %s", result)
        reply = {}
        if "Failed to execute command" in result:
            reply["status"] = "error"
            reply["message"] = f"Error: {result}"
        elif "Unknown command" in result:
            reply["status"] = "error"
            reply["message"] = "Unknown command"
        else:
            if command == "custom":
                reply_message = (
                    f'Custom Command "{rcon_command} {message}" executed successfully'
                    + f". Result:\n{result}"
                )
            else:
                reply_message = (
                    f'Command "{command}{" " + message if message else ""}" '
                    + f"executed successfully. Result:\n{result}"
                )
            reply["status"] = "success"
            reply["message"] = reply_message
        return reply


SECTION_SIGN = "§"
RESET = "\u001B[0m"

# Regex for IPv4 addresses
IPV4_PATTERN = r"^(\d{1,3}\.){3}\d{1,3}$"

# Regex for domain names (simplified version)
DOMAIN_PATTERN = r"^([a-z0-9]+(-[a-z0-9]+)*\.)+([a-z]{2,})$"

colors = {
    "0": "\u001B[30m",  # black
    "1": "\u001B[34m",  # dark blue
    "2": "\u001B[32m",  # dark green
    "3": "\u001B[36m",  # dark aqua
    "4": "\u001B[31m",  # dark red
    "5": "\u001B[35m",  # dark purple
    "6": "\u001B[33m",  # gold
    "7": "\u001B[37m",  # gray
    "8": "\u001B[90m",  # dark gray
    "9": "\u001B[94m",  # blue
    "a": "\u001B[92m",  # green
    "b": "\u001B[96m",  # aqua
    "c": "\u001B[91m",  # red
    "d": "\u001B[95m",  # light purple
    "e": "\u001B[93m",  # yellow
    "f": "\u001B[97m",  # white
    "k": "",  # random (obfuscated)
    "l": "\u001B[1m",  # bold
    "m": "\u001B[9m",  # strikethrough
    "n": "\u001B[4m",  # underline
    "o": "\u001B[3m",  # italic
    "r": RESET,  # reset
}


class RconError(Exception):
    """Custom exception class for RCON errors."""


class RemoteConsole:
    """Class to establish and manage a remote console connection."""

    def __init__(self, host, port, password):
        """
        Initialize a RemoteConsole object.

        Args:
            host (str): The host (IP address or hostname) of the RCON server.
            port (int): The port of the RCON server.
            password (str): The RCON password for authentication.

        Raises:
            RconError: If authentication fails or there is an issue with the connection.
        """
        self.conn = socket.create_connection((host, port), timeout=10)
        self.lock = threading.Lock()
        self.reqid = 0x7FFFFFFF

        # Authenticate
        if not self._authenticate(password):
            raise RconError("Authentication failed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _authenticate(self, password):
        """
        Authenticate with the RCON server using the provided password.

        Args:
            password (str): The RCON password for authentication.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        # Use a distinct request ID for authentication, separate from regular command IDs
        auth_reqid = -1  # Or any other suitable constant or unique value
        self._write_cmd(
            3, password, auth_reqid
        )  # cmdAuth = 3, sending with auth_reqid

        # Read the authentication response
        resp_type, resp_reqid, _ = self._read_response()

        if resp_type != 2 or resp_reqid != auth_reqid:  # respAuthResponse = 2
            return False  # Authentication failed

        return True  # Authentication successful

    def write(self, cmd):
        """
        Send a command to the RCON server.

        Args:
            cmd (str): The command to send.

        Returns:
            int: The request ID for the sent command.
        """
        return self._write_cmd(2, cmd)  # cmdExecCommand = 2

    def read(self):
        """
        Read the response from the RCON server.

        Returns:
            tuple: A tuple containing the response type, request ID, and response data.
        """
        return self._read_response()

    def close(self):
        """Close the connection to the RCON server."""
        self.conn.close()

    def _new_request_id(self):
        """
        Generate a new request ID for RCON commands.

        Returns:
            int: The generated request ID.
        """
        self.reqid = (self.reqid + 1) & 0x0FFFFFFF
        return self.reqid

    def _write_cmd(self, cmd_type, cmd_str, reqid=None):
        """
        Write a command to the RCON server.

        Args:
            cmd_type (int): The command type.
            cmd_str (str): The command string.
            reqid (int, optional): The request ID. If not provided, a new one will be generated.

        Returns:
            int: The request ID for the sent command.
        """
        if len(cmd_str) > 1024 - 10:
            raise RconError("Command too long")

        if reqid is None:
            reqid = self._new_request_id()

        packet = struct.pack("<iii", 10 + len(cmd_str), reqid, cmd_type)
        # The original ascii encoding, try utf-8 instead
        packet += cmd_str.encode("utf-8") + b"\x00\x00"
        # packet += cmd_str.encode("ascii") + b"\x00\x00"

        with self.lock:
            self.conn.sendall(packet)

        return reqid

    def _read_response(self):
        """
        Read the response from the RCON server.

        Returns:
            tuple: A tuple containing the response type, request ID, and response data.
        """
        with self.lock:
            # Read packet length (first 4 bytes)
            size_data = self.conn.recv(4)
            if len(size_data) < 4:
                raise RconError("Incomplete response")

            size = struct.unpack("<i", size_data)[0]
            if size < 10 or size > 4096:
                raise RconError("Invalid response size")

            # Read the rest of the packet
            remaining_data = self.conn.recv(size)
            reqid, resp_type = struct.unpack("<ii", remaining_data[:8])

            # Extract the actual response data
            # Adjusting the offset here if necessary
            response = (
                remaining_data[8:]
                # Original ascii decoding, try utf-8 instead
                .decode("utf-8", errors="ignore").rstrip("\x00")
                # .decode("ascii", errors="ignore").rstrip("\x00")
            )

            # function for checking if the response is base64 encoded
            def is_base64_encoded(s):
                try:
                    _ = base64.b64decode(s).decode("utf-8")
                    return True
                except Exception:  # pylint: disable=broad-except
                    return False

            # print(f"Original Response: {response}")

            # if the response is base64 encoded, decode it
            if is_base64_encoded(response):
                response = base64.b64decode(response).decode("utf-8")
                # print(f"Decoded Response: {response}")

            return resp_type, reqid, response


def colorize(s):
    """
    Apply Minecraft-style color codes to a string.

    Args:
        s (str): The input string containing color codes.

    Returns:
        str: The string with color codes applied.
    """
    if platform.system() == "Windows":
        return s

    for code, color in colors.items():
        s = s.replace(SECTION_SIGN + code, color)
    s = s.replace("\n", "\n" + RESET)
    return s


def start(host_port, password):
    """
    Start a command-line interface for interacting with the RCON server.

    Args:
        host_port (str): The host and port of the RCON server in the format "host:port".
        password (str): The RCON password for authentication.
    """
    host, port = host_port.split(":")
    port = int(port)

    try:
        with RemoteConsole(host, port, password) as remote_console:
            while True:
                try:
                    cmd = input("> ")
                    if not cmd:
                        break

                    req_id = remote_console.write(cmd)
                    _, resp_req_id, data = remote_console.read()
                    if req_id != resp_req_id:
                        print(
                            "Error: Invalid Password?",
                            file=sys.stderr,
                        )

                    print(colorize(data))
                except EOFError:
                    break
                except Exception as e:  # pylint: disable=broad-except
                    print(f"Failed to read command: {e}", file=sys.stderr)
    except Exception as e:  # pylint: disable=broad-except
        print(f"Failed to connect to RCON server: {e}", file=sys.stderr)


def execute(host_port: str, password, *command, base64_encoded: bool = False):
    """
    Execute one or more commands on the RCON server.

    Args:
        host_port (str): The host and port of the RCON server in the format "host:port".
        password (str): The RCON password for authentication.
        *commands (str): The commands to send to the RCON server.
    """
    host, port = host_port.split(":")
    port = int(port)
    command = " ".join(command)

    # Replace spaces with a non-breaking space (ASCII 160) or unit separator (ASCII 31)
    # Here, we use the unit separator as an example
    if command.lower().startswith("broadcast "):
        parts = command.split(" ", 1)  # Split into 'Broadcast' and the message
        command = (
            # parts[0] + " " + parts[1].replace(" ", "\x1F")
            parts[0]
            + " "
            + parts[1].replace(" ", "\u001f")
        )  # Replace spaces in the message

    # If the command starts with 'shutdown',
    # replace all spaces after the second with a unit separator
    if command.lower().startswith("shutdown"):
        parts = command.split(
            " ", 2
        )  # Split into 'shutdown', 'delay', and 'message'
        command = (
            parts[0] + " " + parts[1] + " " + parts[2].replace(" ", "\x1F")
        )  # Replace spaces in the message

    if base64_encoded:
        command = base64.b64encode(command.encode("utf-8")).decode("utf-8")

    try:
        with RemoteConsole(host, port, password) as remote_console:
            req_id = remote_console.write(command)
            _, resp_req_id, data = remote_console.read()
            if req_id != resp_req_id:
                return "Error: Invalid Password?"

            # print(colorize(data))
            return data
    except Exception as e:  # pylint: disable=broad-except
        return f"Failed to execute command: {e}"


def resolve_address(ip_or_domain):
    """Determine if input is an IP address, a domain name, or neither, and resolve if necessary.

    Args:
        ip_or_domain (str): The input IP address or domain name.

    Returns:
        str: The IP address if resolution is successful or the original IP if already an IP address.
    """
    # Check if the input is an IPv4 address
    if re.match(IPV4_PATTERN, ip_or_domain, re.IGNORECASE):
        return ip_or_domain  # It's already an IP address, return as is

    # Check if the input is a domain name (including subdomains)
    elif re.match(DOMAIN_PATTERN, ip_or_domain, re.IGNORECASE):
        try:
            ip = socket.gethostbyname(ip_or_domain)
            return ip
        except socket.gaierror as exc:
            return f"Error resolving domain: {exc}"

    # If neither, raise an error
    else:
        return f"Error: Invalid IP address or domain name: {ip_or_domain}"
