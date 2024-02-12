"""RCON Module for handling RCON commands to a DayZ server."""

import logging
from queue import Queue
import threading

from rcon.rcon import execute, resolve_address

from settings import app_settings


def execute_rcon(ip_address, port, password, command, queue) -> None:
    """Execute the specified RCON command and put the result in the queue."""
    log = False
    if log:
        logging.info("Executing RCON command: %s", command)
    if not app_settings.localserver.connected:
        try:
            resolved_ip = resolve_address(ip_address)
            app_settings.localserver.ip = resolved_ip
            logging.info("Resolved IP: %s", resolved_ip)
        except ValueError as e:
            logging.info("Error: %s", e)
    else:
        resolved_ip = app_settings.localserver.ip
        if log:
            logging.info("Using cached IP: %s", resolved_ip)
    host_port = f"{resolved_ip}:{port}"
    result = execute(host_port, password, command).strip()
    if log:
        logging.info("Command Output: %s\n", result)
    if result:
        queue.put(result.strip())


def rcon_broadcast(ip_address, port, password, message) -> dict:
    """Broadcast the specified message to the server."""
    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(
            ip_address,
            port,
            password,
            f"broadcast {message}",
            result_queue,
        ),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    info = f"RCON Broadcast Result: {result}"
    logging.info(info)
    reply = {}
    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = "Broadcast Error"
    else:
        reply["status"] = "success"
        reply["message"] = "Broadcast sent successfully"

    return reply


def rcon_connect(ip_address, port, password) -> dict:
    """Connect to the RCON server and retrieve the server name and version."""
    result_queue = Queue()
    command_thread = threading.Thread(
        target=execute_rcon,
        args=(ip_address, port, password, "Info", result_queue),
    )
    command_thread.start()
    command_thread.join()  # Wait for the thread to complete

    # Retrieve the result from the queue
    result = result_queue.get()
    info = f"RCON Connection Result: {result}"
    logging.info(info)
    reply = {}
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
        reply["message"] = "Connected to server successfully"
        reply["server_name"] = result.split("]")[1].strip()
        reply["server_version"] = result.split("[")[1].split("]")[0].strip()

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
    info = f"RCON Shutdown Result: {result}"
    logging.info(info)
    reply = {}
    if "Failed to execute command" in result:
        reply["status"] = "error"
        reply["message"] = "Shutdown Error"
    else:
        reply["status"] = "success"
        reply["message"] = "Server shutdown initiated successfully"

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
