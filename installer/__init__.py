"""Installer package."""

import logging
import os
import platform
import shutil
import subprocess
import time
import zipfile

import settings as s

from helper.multiprocess import run_function_on_process
from helper.networking import get_public_ip, get_local_ip
from helper.processhandling import (
    terminate_process_by_pid,
    identify_process_by_name,
)
from rcon import rcon_connect, rcon_doexit, rcon_save


def check_install() -> dict:
    """Check if steamcmd is installed."""
    steamcmd_result = {}
    os_result = {}
    palserver_result = {}
    final_result = {}
    # Find out current OS: Windows, Linux, or macOS
    try:
        os_name = platform.system()
        os_result["status"] = "success"
        os_result["value"] = f"{os_name}"
        s.server_os = os_name
        # logging.info(os_result)
    except Exception as e:  # pylint: disable=broad-except
        os_result["status"] = "error"
        os_result["value"] = "Error checking OS."
        info = f"Error checking OS: {e}"
        logging.info(info)
    # Check if steamcmd is installed
    try:
        if os.path.isfile("steamcmd/steamcmd.exe"):
            steamcmd_result["status"] = "success"
            steamcmd_result["value"] = True
            # logging.info(steamcmd_result)
        else:
            steamcmd_result["status"] = "success"
            steamcmd_result["value"] = False
            # logging.info(steamcmd_result)
    except Exception as e:  # pylint: disable=broad-except
        steamcmd_result["status"] = "error"
        steamcmd_result["value"] = "Error checking SteamCMD installation."
        info = f"Error checking SteamCMD installation: {e}"
        logging.info(info)
    # Check if PalServer is installed
    if s.server_os == "Windows":
        path_to_check = s.WINDOWS_PALWORLD_SETTINGS_INI_PATH
    else:
        path_to_check = s.LINUX_PALWORLD_SETTINGS_INI_PATH
    try:
        if os.path.isfile(path_to_check):
            # Check if the file is not empty
            palserver_result["status"] = "success"
            palserver_result["value"] = True
            # logging.info(palserver_result)
        else:
            palserver_result["status"] = "success"
            palserver_result["value"] = False
            # logging.info(palserver_result)
    except Exception as e:  # pylint: disable=broad-except
        palserver_result["status"] = "error"
        palserver_result["value"] = "Error checking PalServer installation."
        info = f"Error checking PalServer installation: {e}"
        logging.info(info)

    if (
        os_result["status"] == "success"
        and steamcmd_result["status"] == "success"
        and palserver_result["status"] == "success"
    ):
        settings_result = read_server_settings()
        if settings_result["status"] == "success":
            final_result["settings"] = settings_result
            final_result["status"] = "success"
    else:
        final_result["status"] = "error"

    final_result["os"] = os_result
    final_result["steamcmd"] = steamcmd_result
    final_result["palserver"] = palserver_result
    # logging.info(final_result)
    return final_result


def install_server() -> dict:
    """Install the server."""
    result = {}
    if s.server_os == "Windows":
        steamcmd_result = install_steamcmd()
        palserver_result = install_palserver()
        saved_data_result = check_for_saved_data()
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
    else:
        # TODO: Add support for Linux and macOS
        pass


def install_steamcmd() -> dict:
    """Install steamcmd."""
    result = {}
    if s.server_os == "Windows":
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
            info = f"Error downloading steamcmd.zip: {e}"
            logging.info(info)
            result["status"] = "error"
            result["message"] = "Error downloading steamcmd.zip"
            return result
        # Unzip steamcmd.zip to steamcmd folder
        try:
            with zipfile.ZipFile("steamcmd.zip", "r") as zip_ref:
                zip_ref.extractall("steamcmd")
            logging.info("Unzip complete.")
        except Exception as e:  # pylint: disable=broad-except
            info = f"Error unzipping steamcmd.zip: {e}"
            logging.info(info)
            result["status"] = "error"
            result["message"] = "Error unzipping steamcmd.zip"
            return result

        # Remove steamcmd.zip
        try:
            os.remove("steamcmd.zip")
            logging.info("Removed steamcmd.zip")
        except Exception as e:  # pylint: disable=broad-except
            info = f"Error removing steamcmd.zip: {e}"
            logging.info(info)
            result["status"] = "error"
            result["message"] = "Error removing steamcmd.zip"
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
    if s.server_os == "Windows":
        # run 'steamcmd +login anonymous +app_update 2394010 validate +quit'
        # in './steamcmd' directory using powershell
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
            logging.info("PalServer installed successfully")
        except subprocess.CalledProcessError as e:
            info = f"Error installing PalServer: {e}"
            logging.info(info)
            result["status"] = "error"
            result["message"] = "Error installing PalServer"
            return result
        result["status"] = "success"
        result["message"] = "PalServer installed successfully"
        return result
    else:
        # TODO: Add support for Linux and macOS
        pass


def check_for_saved_data() -> dict:
    """Check for saved data."""
    result = {}
    # Check if steamcmd/steamapps/common/PalServer/Saved path exists
    try:
        if os.path.isdir("steamcmd/steamapps/common/PalServer/Saved"):
            result["status"] = "success"
            result["value"] = True
            logging.info(result)
        else:
            result["status"] = "success"
            result["value"] = False
            logging.info(result)
            return result
    except Exception as e:  # pylint: disable=broad-except
        result["status"] = "error"
        result["value"] = "Error checking for saved data."
        info = f"Error checking for saved data: {e}"
        logging.info(info)
        return result


def run_server(launcher_args: dict = None):
    """Run the server."""
    result = {}
    info = f"Running server. Launcher Args: {launcher_args}"
    logging.info(info)
    epicapp = launcher_args["epicApp"]
    useperfthreads = launcher_args["useperfthreads"]
    noasyncloadingthread = launcher_args["NoAsyncLoadingThread"]
    usemultithreadfords = launcher_args["UseMultithreadForDS"]
    base_cmd = "steamcmd/steamapps/common/PalServer/PalServer.exe"    
    info = f"Running server. Command: {base_cmd}"
    logging.info(info)
    # Construct the command with necessary parameters and flags, add - for all flags except epicapp
    cmd = f'"{base_cmd}"{" EpicApp=Palserver" if epicapp else ""}{" -useperfthreads" if useperfthreads else ""}{" -NoAsyncLoadingThread" if noasyncloadingthread else ""}{" -UseMultithreadForDS" if usemultithreadfords else ""}' # pylint: disable=line-too-long
    # cmd = f'cmd /c start "PalServer" "{base_cmd}"' # pylint: disable=line-too-long

    try:
        info = f"Starting server. Command: {cmd}"
        logging.info(info)
        # Start the process and return the process object itself
        subprocess.Popen(cmd, shell=True)
        result["status"] = "success"
        result["message"] = "Server started successfully"
        return result
    except Exception as e:  # pylint: disable=broad-except
        info = f"Error starting server: {e}"
        logging.error(info)
        result["status"] = "error"
        result["message"] = "Error starting server"
        return result


def delete_existing_settings():
    """Delete existing settings on the server."""
    result = {}
    if s.server_os == "Windows":
        try:
            logging.info("Deleting existing settings on the server")
            # Check that file exists
            if os.path.isfile("steamcmd/steamapps/common/PalServer/Pal/Saved/Config/WindowsServer/PalWorldSettings.ini"): # pylint: disable=line-too-long
                os.remove("steamcmd/steamapps/common/PalServer/Pal/Saved/Config/WindowsServer/PalWorldSettings.ini") # pylint: disable=line-too-long
                # Check that file was deleted
                if not os.path.isfile("steamcmd/steamapps/common/PalServer/Pal/Saved/Config/WindowsServer/PalWorldSettings.ini"): # pylint: disable=line-too-long
                    logging.info("Existing settings deleted from the server")
                    result["status"] = "success"
                    result["message"] = "Existing settings deleted from the server"
                    return result
            else:
                result["status"] = "success"
                result["message"] = "No existing settings found on the server"
                logging.info(result)
                return result
        except Exception as e:  # pylint: disable=broad-except
            info = f"Error deleting existing settings on the server: {e}"
            logging.error(info)
            result["status"] = "error"
            result["message"] = "Error deleting existing settings on the server"
            return result
    else:
        # TODO: Add support for Linux and macOS
        pass


def copy_default_settings():
    """Copy default settings to the server."""
    result = {}
    if s.server_os == "Windows":
        # Delete existing settings        
        if os.path.isfile("steamcmd/steamapps/common/PalServer/DefaultPalWorldSettings.ini"):
            # Copy default settings to the server
            try:
                logging.info("Copying default settings to the server")
                shutil.copy("steamcmd/steamapps/common/PalServer/DefaultPalWorldSettings.ini", "steamcmd/steamapps/common/PalServer/Pal/Saved/Config/WindowsServer/PalWorldSettings.ini") # pylint: disable=line-too-long
                logging.info("Default settings copied to the server")
                result["status"] = "success"
                result["message"] = "Default settings copied to the server"
                return result
            except Exception as e:  # pylint: disable=broad-except
                info = f"Error copying default settings to the server: {e}"
                logging.error(info)
                result["status"] = "error"
                result["message"] = "Error copying default settings to the server"
                return result
        else:
            result["status"] = "error"
            result["message"] = "Default settings file not found"
            return result
    else:
        # TODO: Add support for Linux and macOS
        pass


def read_server_settings():
    """Read server settings from the settings file."""
    result = {}
    if s.server_os == "Windows":
        settings_file_path = s.WINDOWS_PALWORLD_SETTINGS_INI_PATH
    else:
        settings_file_path = s.LINUX_PALWORLD_SETTINGS_INI_PATH
    try:
        with open(settings_file_path, 'r', encoding="utf-8") as file:
            lines = file.readlines()
            result["status"] = "success"
            result["value"] = lines
            logging.info("Read settings file successfully.")
    except Exception as e:  # pylint: disable=broad-except
        info = f"Error reading settings file: {e}"
        logging.error(info)
        result["status"] = "error"
        result["value"] = "Error reading settings file"
        return result
    
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
                
                local_ip = get_local_ip()
                if not local_ip:
                    result["status"] = "error"
                    result["message"] = "Error getting local IP address"
                    return result
                result["settings"]["LocalIP"] = local_ip
                return result
    except Exception as e:  # pylint: disable=broad-except
        info = f"Error processing settings file: {e}"
        logging.error(info)
        result["status"] = "error"
        result["value"] = "Error processing settings file"
        return result

def update_palworld_settings_ini(settings_to_change: dict = None):
    """Enable RCON on the server."""
    result = {}    
    
    if settings_to_change is None:
        result["status"] = "error"
        result["message"] = "No settings to change provided"
        return result
    
    info = f"Settings to change: {settings_to_change}"
    logging.info(info)
    
    public_ip = get_public_ip()
    if not public_ip:
        result["status"] = "error"
        result["message"] = "Error getting public IP address"
        return result
    
    if settings_to_change["RCONEnabled"] == "true":
        settings_to_change["RCONEnabled"] = "True"
    elif settings_to_change["RCONEnabled"] == "false":
        settings_to_change["RCONEnabled"] = "False"
    
    settings_to_change["PublicIP"] = f'"{public_ip}"'
    
    if s.server_os == "Windows":
        settings_file_path = s.WINDOWS_PALWORLD_SETTINGS_INI_PATH
    else:
        settings_file_path = s.LINUX_PALWORLD_SETTINGS_INI_PATH
        
    # Check that settings file exists        
    if os.path.isfile(settings_file_path):
        logging.info("Found settings file. Enabling RCON.")
        try:
            with open(settings_file_path, 'r', encoding="utf-8") as file:
                lines = file.readlines()
                logging.info("Read settings file successfully.")
        except Exception as e:  # pylint: disable=broad-except
            result["status"] = "error"
            result["message"] = "Error reading settings file"
            info = f"Error reading settings file: {e}"
            logging.error(info)
            return result
        
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
            with open(settings_file_path, 'w', encoding="utf-8") as file:
                file.writelines(lines)
            
            result["status"] = "success"
            result["message"] = "RCON enabled successfully"
            return result
        except Exception as e: # pylint: disable=broad-except
            info = f"Error writing settings file: {e}"
            logging.error(info)
            result["status"] = "error"
            result["message"] = "Error writing settings file"
            return result


def first_run():
    
    """Run server after clean install to create initial files."""
    result = {}
    if s.server_os == "Windows":
        logging.info("Running server for the first time to create initial files.")
        launcher_args = {
            "epicApp": False,
            "useperfthreads": False,
            "NoAsyncLoadingThread": False,
            "UseMultithreadForDS": False,
        }
        run_function_on_process(run_server, launcher_args)
        time.sleep(3)
        identified = identify_process_by_name("PalServer-Win64-Test-Cmd")
        if identified["status"] == "success":
            info = f"Server Process ID: {identified["value"]}"
            logging.info(info)
            pid = identified["value"]
            logging.info("Giving server 10 seconds to fully start, before shutting it down")
            time.sleep(5)
            terminated = terminate_process_by_pid(pid)
            if terminated:
                deleted = delete_existing_settings()
                if deleted["status"] == "success":
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
                    result["message"] = "Error deleting existing settings on the server"
                    return result                
            else:
                result["status"] = "error"
                result["message"] = "Error terminating server"
                return result
        else:
            result["status"] = "error"
            result["message"] = "Error identifying server process"
            return result
    else:
        # TODO: Add support for Linux and macOS
        pass
