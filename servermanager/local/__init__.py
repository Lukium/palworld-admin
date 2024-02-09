"""Installer package."""

import logging
import os
import re
import shutil
import subprocess
import time
import zipfile

# import settings as s
from settings import app_settings

from helper.fileprocessing import file_to_lines
from helper.networking import get_public_ip, get_local_ip


def check_os() -> dict:
    """Check the OS."""
    result = {}
    os_name = app_settings.app_os
    result["status"] = "success"
    result["value"] = f"{os_name}"
    logging.info("OS reply to UI: %s", result)
    return result


def check_steamcmd_install() -> dict:
    """Check if steamcmd is installed."""
    result = {}
    # Check if steamcmd is installed
    try:
        logging.info("Checking SteamCMD installation in %s",
                     app_settings.localserver.steamcmd_path)
        if os.path.isfile(app_settings.localserver.steamcmd_path):
            result["status"] = "success"
            result["value"] = True
            app_settings.localserver.steamcmd_installed = True
            logging.info("SteamCMD reply to UI: %s", result)
        else:
            result["status"] = "success"
            result["value"] = False
            app_settings.localserver.steamcmd_installed = False
            logging.info("SteamCMD reply to UI: %s", result)
    except Exception as e:  # pylint: disable=broad-except
        result["status"] = "error"
        result["value"] = "Error checking SteamCMD installation."
        logging.info("Error checking SteamCMD installation: %s", e)
    return result


def check_palworld_install() -> dict:
    """Check if PalWorld is installed."""
    result = {}
    # Check if PalWorld is installed
    try:
        logging.info("Checking PalWorld installation in %s", app_settings.localserver.ini_path)
        if os.path.isfile(app_settings.localserver.ini_path):
            # Check if the file is not empty by reading the file and checking for content
            with open(app_settings.localserver.ini_path, 'r', encoding="utf-8") as file:
                file_content = file.read()
            # Remove leading and trailing whitespace
            file_content = file_content.strip()
            if len(file_content) > 0:
                result["status"] = "success"
                result["value"] = True
            else:
                result["status"] = "success"
                result["value"] = False
            logging.info("PalWorld reply to UI: %s", result)
        else:
            result["status"] = "success"
            result["value"] = False
            logging.info("PalWorld reply to UI: %s", result)
    except Exception as e:  # pylint: disable=broad-except
        result["status"] = "error"
        result["value"] = "Error checking PalWorld installation."
        logging.info("Error checking PalWorld installation: %s", e)
    return result


def check_server_running() -> dict:
    """Check if the server is running."""
    result = {}
    try:
        identified = identify_process_by_name("PalServer-Win64-Test-Cmd")
        if identified["status"] == "success":
            if identified["value"] != "No matching processes found.":
                result["status"] = "success"
                result["value"] = True
                app_settings.localserver.running = True
                logging.info("Server is running: %s", result)
            else:
                result["status"] = "success"
                result["value"] = False
                app_settings.localserver.running = False
                logging.info("Server is not running: %s", result)
        else:
            result["status"] = "error"
            result["value"] = "Error identifying server process"
            logging.info("Error identifying server process: %s", identified)
    except Exception as e:  # pylint: disable=broad-except
        result["status"] = "error"
        result["value"] = "Error checking if server is running"
        logging.info("Error checking if server is running: %s", e)
    return result


def check_install() -> dict:
    """Check if steamcmd is installed."""
    # Set the working server to Local
    app_settings.set_working_server("Local")

    result = {} # Final result to be returned

    # Check Installation
    os_result = check_os()
    steamcmd_result = check_steamcmd_install()
    palserver_result = check_palworld_install()
    result_running = check_server_running()

    if (
        os_result["status"] == "success"
        and steamcmd_result["status"] == "success"
        and palserver_result["status"] == "success"
    ):
        # Combine the results
        result["status"] = "success"
        result["os"] = os_result
        result["steamcmd"] = steamcmd_result
        result["palserver"] = palserver_result
        result["running"] = result_running

        # If both SteamCMD and PalServer are installed, read the settings
        if steamcmd_result["value"] is True and palserver_result["value"] is True:
            logging.info("SteamCMD and PalServer are installed, reading settings.")
            result["settings"] = read_server_settings()
    else:
        result["status"] = "error"
        result["message"] = "Error checking installation"
        logging.info("Error checking installation: %s", result)
    return result


def read_server_settings():
    """Read server settings from the settings file."""
    result = {}
    logging.info("Reading settings file from %s", app_settings.localserver.ini_path)
    try:
        with open(app_settings.localserver.ini_path, 'r', encoding="utf-8") as file:
            lines = file.readlines()
            result["status"] = "success"
            result["value"] = lines
            logging.info("Read settings file successfully.")
    except Exception as e:  # pylint: disable=broad-except
        result["status"] = "error"
        result["value"] = "Error reading settings file"
        logging.error("Error reading settings file: %s", e)
        return result
    # Extract the settings from the settings file
    try:
        for _, line in enumerate(lines):
            if line.startswith("OptionSettings="):
                # Extract the settings string
                settings_line = line
                settings_string = settings_line[settings_line.find("(")+1:settings_line.find(")")]

                # Break down and sort the settings
                settings = settings_string.split(",")
                settings_dict = {}
                for setting in settings:
                    key = setting.split("=")[0]
                    value = setting.split("=")[1]
                    settings_dict[key] = value
                result["status"] = "success"
                result["settings"] = settings_dict
                # Get the local IP address
                local_ip = get_local_ip()
                if not local_ip:
                    result["status"] = "error"
                    result["message"] = "Error getting local IP address"
                result["settings"]["LocalIP"] = local_ip
    except Exception as e:  # pylint: disable=broad-except
        result["status"] = "error"
        result["value"] = "Error processing settings file"
        logging.error("Error processing settings file: %s", e)
    return result


def backup_server() -> dict:
    """Backup the server data."""
    result = {}
    logging.info("Backing up server data from %s to %s", app_settings.localserver.data_path, app_settings.localserver.backup_path)
    backup_path = app_settings.localserver.backup_path
    data_path = app_settings.localserver.data_path
    try:
        # Check if the backup path exists, if not create it
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
            logging.info("Created backup path: %s", backup_path)
        # Create a timestamp for the backup
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        # Create the backup folder
        backup_folder = os.path.join(backup_path, f"{timestamp}", "Saved")
        logging.info("Created backup folder: %s", backup_folder)
        # Copy the data to the backup folder
        shutil.copytree(data_path, backup_folder)
        # Verify that the data was copied by comparing the contents of the data and backup folders
        data_contents = os.listdir(data_path)
        backup_contents = os.listdir(backup_folder)
        if data_contents == backup_contents:
            result["status"] = "success"
            result["message"] = "Server data backed up successfully"
            logging.info("Copied data to backup folder: %s", backup_folder)
        else:
            # If the contents of the data and backup folders do not match, delete the backup folder
            if os.path.exists(backup_folder):
                shutil.rmtree(backup_folder)
            result["status"] = "error"
            result["message"] = "Error backing up server data"
            logging.error("Error backing up server data")
    except Exception as e:  # pylint: disable=broad-except
        result["status"] = "error"
        result["message"] = "Exception while backing up server data"
        logging.error("Exception while backing up server data: %s", e)
    return result


def install_server() -> dict:
    """Install the server."""
    result = {}
    if not app_settings.localserver.steamcmd_installed:
        steamcmd_result = install_steamcmd()
    else:
        steamcmd_result = {"status": "success", "message": "SteamCMD already installed"}
    palserver_result = install_palserver()
    saved_data_result = check_palworld_install()
    result["steamcmd"] = steamcmd_result
    result["palserver"] = palserver_result
    result["saved_data"] = saved_data_result
    if (
        steamcmd_result["status"] == "success"
        and palserver_result["status"] == "success"
    ):
        result["status"] = "success"
        result["message"] = "Server installed successfully"
    if saved_data_result["value"] is False:
        first_run_result = first_run()
        result["first_run"] = first_run_result
        if first_run_result["status"] == "success":
            result["status"] = "success"
            result["message"] = "Server installed successfully"
    return result


def install_steamcmd() -> dict:
    """Install steamcmd."""
    result = {}
    if app_settings.app_os == "Windows":
        try:
            # Use Powershell to Download steamcmd from
            # https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip
            logging.info("Downloading steamcmd.zip")
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "Invoke-WebRequest -Uri https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip -OutFile steamcmd.zip", # pylint: disable=line-too-long
                ],
                check=True,
            )
            logging.info("Download complete.")
        except subprocess.CalledProcessError as e:
            result["status"] = "error"
            result["message"] = "Error downloading steamcmd.zip"
            logging.info("Error downloading steamcmd.zip: %s", e)
            return result
        # Unzip steamcmd.zip to steamcmd folder
        try:
            with zipfile.ZipFile("steamcmd.zip", "r") as zip_ref:
                zip_ref.extractall("steamcmd")
            logging.info("Unzip complete.")
        except Exception as e:  # pylint: disable=broad-except
            result["status"] = "error"
            result["message"] = "Error unzipping steamcmd.zip"
            logging.info("Error unzipping steamcmd.zip: %s", e)
            return result

        # Remove steamcmd.zip
        try:
            os.remove("steamcmd.zip")
            logging.info("Removed steamcmd.zip")
        except Exception as e:  # pylint: disable=broad-except
            result["status"] = "error"
            result["message"] = "Error removing steamcmd.zip"
            logging.info("Error removing steamcmd.zip: %s", e)
            return result

        result["status"] = "success"
        result["message"] = "SteamCMD installed successfully"
        return result

    else:
        # TODO: Add support for Linux and macOS
        pass


def install_palserver():
    """Install PalServer."""
    result = {}
    if app_settings.app_os == "Windows":
        try:
            logging.info("Installing PalServer")
            subprocess.run(
                [
                    "powershell",
                    "-Command",
                    "cd steamcmd; ./steamcmd.exe +login anonymous +app_update 2394010 validate +quit", # pylint: disable=line-too-long
                ],
                check=True,
            )
            result["status"] = "success"
            result["message"] = "PalServer installed successfully"
            logging.info("PalServer installed successfully")
        except subprocess.CalledProcessError as e:
            result["status"] = "error"
            result["message"] = "Error installing PalServer"
            logging.info("Error installing PalServer: %s", e)
        return result

    else:
        # TODO: Add support for Linux and macOS
        pass

def run_server(launcher_args: dict = None):
    """Run the server."""
    result = {}
    logging.info("Running server. Launcher Args: %s", launcher_args)
    epicapp = launcher_args["epicApp"]
    useperfthreads = launcher_args["useperfthreads"]
    noasyncloadingthread = launcher_args["NoAsyncLoadingThread"]
    usemultithreadfords = launcher_args["UseMultithreadForDS"]
    launch_RCON = launcher_args["launch_RCON"]
    auto_backup = launcher_args["auto_backup"]
    auto_backup_delay = launcher_args["auto_backup_delay"]
    # Construct the command with necessary parameters and flags, add - for all flags except epicapp
    cmd = f'"{app_settings.localserver.launcher_path}"{" EpicApp=Palserver" if epicapp else ""}{" -useperfthreads" if useperfthreads else ""}{" -NoAsyncLoadingThread" if noasyncloadingthread else ""}{" -UseMultithreadForDS" if usemultithreadfords else ""}' # pylint: disable=line-too-long
    info = f"Running server. Command: {cmd}"

    try:
        info = f"Starting server. Command: {cmd}"
        logging.info(info)
        # Start the process and return the process object itself
        subprocess.Popen(cmd, shell=True)
        result["status"] = "success"
        result["message"] = "Server started successfully"
        app_settings.localserver.running = True
    except Exception as e:  # pylint: disable=broad-except
        info = f"Error starting server: {e}"
        logging.error(info)
        result["status"] = "error"
        result["message"] = "Error starting server"
    return result


def delete_existing_settings():
    """Delete existing settings on the server."""
    result = {}
    try:
        logging.info("Deleting existing settings on the server")
        # Check that file exists
        settings_file = app_settings.localserver.ini_path
        if os.path.isfile(settings_file):
            os.remove(settings_file)
            # Check that file was deleted
            if not os.path.isfile(settings_file):
                result["status"] = "success"
                result["message"] = "Existing settings deleted from the server"
                logging.info("Existing settings deleted from the server")
        else:
            result["status"] = "success"
            result["message"] = "No existing settings found on the server"
            logging.info("No existing settings found on the server")
    except Exception as e:  # pylint: disable=broad-except
        info = f"Error deleting existing settings on the server: {e}"
        logging.error(info)
        result["status"] = "error"
        result["message"] = "Error deleting existing settings on the server"
    return result


def copy_default_settings():
    """Copy default settings to the server."""
    result = {}
    default_file = app_settings.localserver.default_ini_path
    settings_file = app_settings.localserver.ini_path
    # Only proceed if the default settings file exists, otherwise return an error
    if os.path.isfile(default_file):

        # Delete existing settings on the server before copying the default settings
        deleted = delete_existing_settings()
        # If there was an error deleting the existing settings, return the error
        if deleted["status"] == "error":
            return deleted

        # Copy default settings to the server
        try:
            logging.info("Copying default settings to the server")
            shutil.copy(default_file, settings_file)
            if os.path.isfile(settings_file):
                result["status"] = "success"
                result["message"] = "Default settings copied to the server"
                logging.info("Default settings copied to the server")
            else:
                result["status"] = "error"
                result["message"] = "Error copying default settings to the server"
                logging.info("Error copying default settings to the server")
        except Exception as e:  # pylint: disable=broad-except
            result["status"] = "error"
            result["message"] = "Error copying default settings to the server"
            logging.error("Error copying default settings to the server: %s", e)
        return result
    else:
        result["status"] = "error"
        result["message"] = "Default settings file not found"
        return result


def update_palworld_settings_ini(settings_to_change: dict = None):
    """Update the PalWorld settings file."""
    result = {}

    if settings_to_change is None:
        result["status"] = "error"
        result["message"] = "No settings to change provided"
        return result

    logging.info("Updating PalWorld settings file. Settings to change:\n%s", settings_to_change)

    public_ip = get_public_ip()
    if not public_ip:
        result["status"] = "error"
        result["message"] = "Error getting public IP address"
        return result
    settings_to_change["PublicIP"] = f'"{public_ip}"'

    if settings_to_change["RCONEnabled"] == "true":
        settings_to_change["RCONEnabled"] = "True"
    elif settings_to_change["RCONEnabled"] == "false":
        settings_to_change["RCONEnabled"] = "False"

    lines: list = []
    lines_read = file_to_lines(app_settings.localserver.ini_path)
    if lines_read["status"] == "error":
        return lines_read
    else:
        lines = lines_read["lines"]

    try:
        for i, line in enumerate(lines):
            if line.startswith("OptionSettings="):
                # Extract the settings string
                settings_line = line
                settings_string = settings_line[settings_line.find("(")+1:settings_line.find(")")]

                # Break down and sort the settings
                settings = settings_string.split(",")
                modified_settings = []
                for setting in settings:
                    key = setting.split("=")[0]
                    value = setting.split("=")[1]
                    active_setting = (key, value)
                    if active_setting[0] in settings_to_change:
                        setting=f"{active_setting[0]}={settings_to_change[active_setting[0]]}"
                        modified_settings.append(setting)
                    else:
                        modified_settings.append(setting)

                # Rebuild the modified settings string
                modified_settings_string = ",".join(modified_settings)
                modified_settings_line = f"OptionSettings=({modified_settings_string})\n"

                # Replace the original line with the modified line
                lines[i] = modified_settings_line
        # Write the updated settings back to the file
        with open(app_settings.localserver.ini_path, 'w', encoding="utf-8") as file:
            file.writelines(lines)

        result["status"] = "success"
        result["message"] = "Settings updated successfully"
        logging.info("Settings updated successfully")
    except Exception as e: # pylint: disable=broad-except
        result["status"] = "error"
        result["message"] = "Error writing settings file"
        logging.error("Error writing settings file: %s", e)
    return result


def first_run():
    """Run server after clean install to create initial files."""
    result = {}
    logging.info("Running server for the first time to create initial files.")
    launcher_args = {
        "epicApp": False,
        "useperfthreads": False,
        "NoAsyncLoadingThread": False,
        "UseMultithreadForDS": False,
        "launch_RCON": False,
        "auto_backup": False,
        "auto_backup_delay": 0,
    }
    run_server(launcher_args)
    time.sleep(10)
    identified = identify_process_by_name("PalServer-Win64-Test-Cmd")
    if identified["status"] == "success":
        info = f"Server Process ID: {identified["value"]}"
        logging.info(info)
        pid = identified["value"]
        logging.info("Giving server 5 seconds to fully start, before shutting it down")
        time.sleep(5)
        terminated = terminate_process_by_pid(pid)
        if terminated:
            copied = copy_default_settings()
            if copied["status"] == "success":
                settings_to_change ={ # Used to enable RCON
                    "RCONEnabled": "True",
                    "AdminPassword": '"admin"',
                }
                rcon_enabled = update_palworld_settings_ini(settings_to_change)
                if rcon_enabled["status"] == "success":
                    result["status"] = "success"
                    result["message"] = "Server installed successfully"
                    return result
                else:
                    result["status"] = "error"
                    result["message"] = "Error enabling RCON on the server"
                    return result
            else:
                result["status"] = "error"
                result["message"] = "Error copying default settings to the server"
                return result
        else:
            result["status"] = "error"
            result["message"] = "Error terminating server"
            return result
    else:
        result["status"] = "error"
        result["message"] = "Error identifying server process"
        return result


def identify_process_by_name(executable_name: str):
    """Identify a process by its executable name."""
    result = {}
    if app_settings.app_os == "Windows":
        find_cmd = f"powershell \"Get-Process | Where-Object {{ $_.Name -eq '{executable_name}' }} | Select-Object Id, Name, MainWindowTitle\""  # pylint: disable=line-too-long
        for n in range(10):
            info = (
                f"Attempt {n+1}/10 to find process by name: {executable_name}"
            )
            logging.info(info)
            try:
                # Find processes
                process = subprocess.run(
                    find_cmd,
                    check=True,
                    shell=True,
                    capture_output=True,
                    text=True,
                )
                if process.stdout:
                    # Extract process IDs
                    pids = re.findall(
                        r"^\s*(\d+)", process.stdout, re.MULTILINE
                    )
                    if len(pids) > 0:
                        pid = pids[0]
                        result["status"] = "success"
                        result["value"] = pid

                    else:
                        result["status"] = "success"
                        result["value"] = "No matching processes found."
                        logging.info("No matching processes found.")
                    return result
            except subprocess.CalledProcessError as e:
                info = f"Failed to execute find command: {e}"
                logging.error(info)
                result["status"] = "error"
                result["value"] = f"Failed to execute find command: {e}"
                return result
            else:
                logging.info(
                    "No matching processes found. Waiting 1 second to try again."
                )
                time.sleep(1)

    else:
        # TODO: Add support for Linux and macOS
        pass


def terminate_process_by_pid(pid: int):
    """Terminate a process by its PID."""
    if app_settings.app_os == "Windows":
        try:
            terminate_cmd = f'powershell "Stop-Process -Id {pid} -Force"'
            subprocess.run(terminate_cmd, check=True, shell=True)
            info = f"Terminated process with ID {pid}."
            app_settings.localserver.running = False
            logging.info(info)
            return True
        except subprocess.CalledProcessError as e:
            info = f"Failed to terminate process with ID {pid}: {e}"
            logging.error(info)
            return False
    else:
        # TODO: Add support for Linux and macOS
        pass


def terminate_process_by_name(executable_name: str):
    """Terminate a process by its executable name."""
    if app_settings.app_os == "Windows":
        find_cmd = f"powershell \"Get-Process | Where-Object {{ $_.Name -eq '{executable_name}' }} | Select-Object Id, Name, MainWindowTitle\""  # pylint: disable=line-too-long

        try:
            # Find processes
            result = subprocess.run(
                find_cmd,
                check=True,
                shell=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                # Extract process IDs
                pids = re.findall(r"^\s*(\d+)", result.stdout, re.MULTILINE)
                info: str = f"Server Process IDs: {pids}"
                logging.info(info)

                for pid in pids:
                    try:
                        # Terminate each process by its PID
                        terminate_cmd = (
                            f'powershell "Stop-Process -Id {pid} -Force"'
                        )
                        subprocess.run(terminate_cmd, check=True, shell=True)
                        info = f"Terminated process with ID {pid}."
                        app_settings.localserver.running = False
                        logging.info(info)
                        return True
                    except subprocess.CalledProcessError as e:
                        info = (
                            f"Failed to terminate process with ID {pid}: {e}"
                        )
                        logging.error(info)
                        return False
            else:
                logging.info("No matching processes found.")
                return False
        except subprocess.CalledProcessError as e:
            info = f"Failed to execute find command: {e}"
            logging.error(info)
            return False
    else:
        # TODO: Add support for Linux and macOS
        pass
