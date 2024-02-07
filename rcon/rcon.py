"""Basic RCON client for servers."""

import argparse
import platform
import re
import socket
import struct
import sys
import threading

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
        packet += cmd_str.encode("ascii") + b"\x00\x00"

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
                .decode("ascii", errors="ignore")
                .rstrip("\x00")
            )

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


def execute(host_port, password, *commands):
    """
    Execute one or more commands on the RCON server.

    Args:
        host_port (str): The host and port of the RCON server in the format "host:port".
        password (str): The RCON password for authentication.
        *commands (str): The commands to send to the RCON server.
    """
    host, port = host_port.split(":")
    port = int(port)
    command = " ".join(commands)

    # Replace spaces with a non-breaking space (ASCII 160) or unit separator (ASCII 31)
    # Here, we use the unit separator as an example
    if command.lower().startswith("broadcast "):
        parts = command.split(" ", 1)  # Split into 'Broadcast' and the message
        command = (
            parts[0] + " " + parts[1].replace(" ", "\x1F")
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

    try:
        with RemoteConsole(host, port, password) as remote_console:
            req_id = remote_console.write(command)
            _, resp_req_id, data = remote_console.read()
            if req_id != resp_req_id:
                print(
                    "Error: Invalid Password?",
                    file=sys.stderr,
                )

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
            raise ValueError(
                f"Could not resolve domain: {ip_or_domain}"
            ) from exc

    # If neither, raise an error
    else:
        raise ValueError(f"Invalid IP address or domain name: {ip_or_domain}")


def parse_cli():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="RCON Client")
    parser.add_argument(
        "-i",
        "--ip",
        required=True,
        help="IP address or domain of the RCON server",
    )
    parser.add_argument(
        "-p", "--port", required=True, type=int, help="Port of the RCON server"
    )
    parser.add_argument(
        "-P", "--password", required=True, help="RCON password"
    )
    parser.add_argument(
        "commands", nargs="*", help="Commands to send to the RCON server"
    )

    arguments = parser.parse_args()

    # Resolve the IP address or domain name to an IP address
    try:
        resolved_ip = resolve_address(arguments.ip)
        arguments.ip = resolved_ip
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)  # Print error message directly
        sys.exit(
            1
        )  # Exit the program with a non-zero exit code to indicate an error

    return arguments


# Example usage
if __name__ == "__main__":
    args = parse_cli()

    address = f"{args.ip}:{args.port}"

    if args.commands:
        execute(address, args.password, *args.commands)
    else:
        start(address, args.password)
