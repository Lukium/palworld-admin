"""RCON Module for handling RCON commands to a DayZ server."""

import logging
from queue import Queue
import os
import subprocess
import threading
import time

from palworld_admin.helper.dbmanagement import save_user_settings_to_db
from palworld_admin.rcon.rcon import execute, resolve_address
from palworld_admin.settings import app_settings


def execute_rcon(ip_address, port, password, command, queue) -> None:
    """Execute the specified RCON command and put the result in the queue."""
    log = False
    if log:
        logging.info("Executing RCON command: %s", command)
    if not app_settings.localserver.connected:
        try:
            resolved_ip = resolve_address(ip_address)
            if "Error" in resolved_ip:
                result = {
                    "status": "error",
                    "message": "Error resolving IP, please try again",
                }
                return result
            app_settings.localserver.ip = resolved_ip
            logging.info("Resolved IP: %s", resolved_ip)
        except ValueError as e:
            logging.info("Error: %s", e)
    else:
        resolved_ip = app_settings.localserver.ip
        if log:
            logging.info("Using cached IP: %s", resolved_ip)
    host_port = f"{resolved_ip}:{port}"
    result = execute(
        host_port,
        password,
        command,
        base64_encoded=app_settings.localserver.base64_encoded,
    ).strip()
    if log:
        logging.info("Command Output: %s\n", result)
    if result:
        queue.put(result.strip())


def rcon_broadcast(ip_address, port, password, message, command: str) -> dict:
    """Broadcast the specified message to the server."""
    result_queue = Queue()

    if command == "broadcast" and app_settings.localserver.palguard_installed:
        rcon_command = "pgbroadcast"
    else:
        rcon_command = command

    command_thread = threading.Thread(
        target=execute_rcon,
        args=(
            ip_address,
            port,
            password,
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
        reply["status"] = "success"
        message = (
            f'Command "{command}{" " + message if message else ""}" '
            + f"executed successfully. Result:\n{result}"
        )
        reply["message"] = message
    return reply


def rcon_connect(ip_address, port, password, skip_save: bool = False) -> dict:
    """Connect to the RCON server and retrieve the server name and version."""
    app_settings.localserver.base64_encoded = False
    reply = {}
    result_queue = Queue()

    # Non-Base64 Connection Attempt
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(ip_address, port, password, "Info", result_queue),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result: str = result_queue.get()
    logging.info("Non-Base64 RCON Connection Result: %s", result)

    if "Unknown command" in result:
        # Switch to Base64 Connection
        app_settings.localserver.base64_encoded = True

        # Base64 Connection Attempt
        command_thread = threading.Thread(
            target=execute_rcon,
            args=(ip_address, port, password, "Info", result_queue),
        )
        command_thread.start()
        command_thread.join()  # Wait for the thread to complete

        # Retrieve the result from the queue
        result: str = result_queue.get()
        logging.info("Base64 RCON Connection Result: %s", result)
    else:
        app_settings.localserver.base64_encoded = False

    # Check for palguard commands
    palguard_commands_queue = Queue()
    palguard_commands_list = []
    final_palguard_commands_list = []
    palguard_commands_thread = threading.Thread(
        target=execute_rcon,
        args=(
            ip_address,
            port,
            password,
            "getrconcmds",
            palguard_commands_queue,
        ),
    )
    palguard_commands_thread.start()
    palguard_commands_thread.join()  # Wait for the thread to complete
    palguard_commands_result: str = palguard_commands_queue.get()
    if "Unknown command" not in palguard_commands_result:
        palguard_commands_list = palguard_commands_result.split(";")
        palguard_commands_list.sort()
        # Remove any empty strings from the list
        palguard_commands_list = [
            command for command in palguard_commands_list if command != ""
        ]
        logging.info("Palguard Commands: %s", palguard_commands_list)
        for command in palguard_commands_list:
            logging.info("Command Type: %s", type(command))
            command_name = command.split(":")[0]
            command_args = command.split(":")[1]
            command_dict = {"name": command_name, "args": command_args}
            final_palguard_commands_list.append(command_dict)
        logging.info("Palguard Commands: %s", final_palguard_commands_list)
        reply["palguard_commands"] = final_palguard_commands_list

    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = (
            f'Connection Error: {result.split(":")[1].strip().capitalize()}'
        )
        reply["server_name"] = "N/A"
        reply["server_version"] = "N/A"
    elif "Error: Invalid Password?" in result:
        reply["status"] = "error"
        reply["message"] = "Connection Error: Bad RCON Password?"
        reply["server_name"] = "N/A"
        reply["server_version"] = "N/A"
    elif "Could not resolve domain" in result:
        reply["status"] = "error"
        reply["message"] = (
            "Connection Error: Could not resolve domain name to a valid IP Address"
        )
        reply["server_name"] = "N/A"
        reply["server_version"] = "N/A"
    else:
        app_settings.localserver.connected = True
        reply["status"] = "success"
        reply["message"] = "RCON Connected!"
        reply["server_name"] = result.split("]")[1].strip()
        reply["server_version"] = result.split("[")[1].split("]")[0].strip()
        reply["base64_encoded"] = app_settings.localserver.base64_encoded

        if not skip_save:
            save_user_settings_to_db(
                {
                    "rcon_last_connection": {
                        "host": ip_address,
                        "port": port,
                        "password": password,
                    }
                }
            )

    return reply


def rcon_fetch_players(ip_address, port, password) -> dict:
    """Fetch the list of players currently connected to the server."""
    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(ip_address, port, password, "ShowPlayers", result_queue),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    reply = {}

    if "Failed to decode base64" in result:
        rcon_connect(ip_address, port, password, skip_save=True)
        return {
            "status": "error",
            "message": "Failed to decode base64, retrying connection...",
        }

    # Use first line of result to determine if the command was successful,
    # expect "name,playeruid,steamid"
    if "name,playeruid,steamid" in result:
        reply["status"] = "success"
        reply["message"] = "Players fetched successfully"
        # Use first line of results as the header, and the rest as the player list
        players = result.split("\n")[1:]
        # Each row is a player, with PlayerName, PlayerUID, and SteamID separated by commas
        player_list = []
        for player in players:
            player_data = player.split(",")
            player_list.append(
                {
                    "name": player_data[0],
                    "playeruid": player_data[1],
                    "steamid": player_data[2],
                }
            )
        reply["player_count"] = len(player_list)
        reply["players"] = player_list
    elif "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = (
            f'Connection Error: {result.split(":")[1].strip().capitalize()}'
        )
        reply["player_count"] = 0
        reply["players"] = []
    else:
        reply["status"] = "error"
        reply["message"] = "Connection Error"
        reply["player_count"] = 0
        reply["players"] = []

    return reply


def rcon_kick_player(ip_address, port, password, player_steamid) -> dict:
    """Kick the player with the specified SteamID from the server."""
    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(
            ip_address,
            port,
            password,
            f"KickPlayer {player_steamid}",
            result_queue,
        ),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    info = f"RCON Kick Player Result: {result}"
    logging.info(info)
    reply = {}
    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = "Kick Error"
    elif "Failed to Kick" in result:
        reply["status"] = "error"
        reply["message"] = "Failed to kick player"
    else:
        reply["status"] = "success"
        reply["message"] = "Player kicked successfully"

    return reply


def rcon_ban_player(ip_address, port, password, player_steamid) -> dict:
    """Ban the player with the specified SteamID from the server."""
    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(
            ip_address,
            port,
            password,
            f"BanPlayer {player_steamid}",
            result_queue,
        ),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    info = f"RCON Ban Player Result: {result}"
    logging.info(info)
    reply = {}
    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = "Ban Error"
    elif "Failed to Ban" in result:
        reply["status"] = "error"
        reply["message"] = "Failed to ban player"
    else:
        reply["status"] = "success"
        reply["message"] = "Player banned successfully"

    return reply


def rcon_save(ip_address, port, password) -> dict:
    """Save the server state."""
    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(ip_address, port, password, "Save", result_queue),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    info = f"RCON Save Result: {result}"
    logging.info(info)
    reply = {}
    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = "Save Error"
    else:
        reply["status"] = "success"
        reply["message"] = "Game saved successfully"

    return reply


def rcon_shutdown(ip_address, port, password, delay, message) -> dict:
    """Shutdown the server gracefully with the specified delay and message."""

    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(
            ip_address,
            port,
            password,
            f"Shutdown {delay} {message}",
            result_queue,
        ),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    logging.info("RCON Shutdown Result: %s", result)

    reply = {}
    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = "Error sending shutdown command"
    else:
        if app_settings.localserver.server_process:
            # This means the server was started by Palworld ADMIN
            logging.info(
                "Shutting Down Server Process: %s",
                app_settings.localserver.server_process,
            )

            shutdown_result_queue = Queue()

            def monitor_server_shutdown(result_queue: Queue):
                """Monitor the server process and wait for it to shut down."""
                shutdown_timer = 0
                # Sleep the amount of time specified in the delay before starting the monitoring
                time.sleep(float(delay))
                while app_settings.localserver.server_process.poll() is None:
                    logging.info(
                        "Waited %s seconds for server to shut down",
                        shutdown_timer,
                    )
                    time.sleep(1)
                    shutdown_timer += 1
                    if shutdown_timer > 30:
                        result_queue.put(False)
                logging.info("Server has shut down, result placed in queue")
                result_queue.put(True)

            shutdown_thread = threading.Thread(
                target=monitor_server_shutdown,
                args=(shutdown_result_queue,),
                daemon=True,
            )
            shutdown_thread.start()
            shutdown_result = shutdown_result_queue.get()
            logging.info("Shutdown Result Queue Received: %s", shutdown_result)

            if shutdown_result:
                reply["status"] = "success"
                reply["message"] = "Server shutdown successfully"
            else:
                reply["status"] = "error"
                reply["message"] = (
                    "Server shutdown command sent successfully, "
                    + "but shutdown monitor did not detect server shutdown"
                )
        else:
            # This means the server was not started by Palworld ADMIN
            # Monitor the server shutdown using its PID app_settings.localserver.pid
            logging.info("Shutting down server not started by Palworld ADMIN")
            logging.info("Server PID: %s", app_settings.localserver.pid)

            shutdown_result_queue = Queue()

            def process_exists(pid):
                """Check if a process exists in a cross-platform manner."""
                try:
                    if app_settings.app_os == "Windows":
                        # Windows-specific method
                        result = subprocess.check_output(
                            ["tasklist", "/fi", f"PID eq {pid}"],
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                        if "No tasks are running" in result:
                            return False
                        else:
                            return True
                    else:
                        # POSIX (Unix, Linux, etc.)
                        os.kill(int(pid), 0)
                except (
                    subprocess.CalledProcessError,
                    ProcessLookupError,
                    OSError,
                ):
                    return False
                return True

            def monitor_server_shutdown(result_queue: Queue):
                """Monitor the server process and wait for it to shut down."""
                logging.info("Monitoring server shutdown")
                shutdown_timer = 0
                while process_exists(app_settings.localserver.pid):
                    logging.info(
                        "Waited %s seconds for server to shut down",
                        shutdown_timer,
                    )
                    time.sleep(1)
                    shutdown_timer += 1
                    if shutdown_timer > 30:
                        result_queue.put(False)
                        break
                logging.info("Server has shut down, result placed in queue")
                result_queue.put(True)

            shutdown_thread = threading.Thread(
                target=monitor_server_shutdown,
                args=(shutdown_result_queue,),
                daemon=True,
            )
            shutdown_thread.start()
            shutdown_result = shutdown_result_queue.get()
            logging.info("Shutdown Result Queue Received: %s", shutdown_result)

            if shutdown_result:
                reply["status"] = "success"
                reply["message"] = "Server shutdown successfully"
            else:
                reply["status"] = "error"
                reply["message"] = (
                    "Server shutdown command sent successfully, "
                    + "but shutdown monitor did not detect server shutdown"
                )

    return reply


def rcon_doexit(ip_address, port, password) -> dict:
    """Shutdown the server."""
    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(ip_address, port, password, "DoExit", result_queue),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    info = f"RCON DoExit Result: {result}"
    logging.info(info)
    reply = {}
    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = "Shutdown Error"
    else:
        reply["status"] = "success"
        reply["message"] = "Server shutdown initiated successfully"

    return reply
