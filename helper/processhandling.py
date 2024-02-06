""" Helper functions for process handling. """

import logging
import re
import subprocess
import time

import settings as s


def identify_process_by_name(executable_name: str):
    """Identify a process by its executable name."""
    result = {}
    if s.server_os == "Windows":
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
                    pid = pids[0]
                    result["status"] = "success"
                    result["value"] = pid
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
    if s.server_os == "Windows":
        try:
            terminate_cmd = f'powershell "Stop-Process -Id {pid} -Force"'
            subprocess.run(terminate_cmd, check=True, shell=True)
            info = f"Terminated process with ID {pid}."
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
    if s.server_os == "Windows":
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
