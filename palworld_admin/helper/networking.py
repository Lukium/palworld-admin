"""This module contains helper functions for networking tasks."""

import logging
import socket

import requests
import os


def get_public_ip():
    """Get the public IP address of the server."""
    logging.info("Getting public IP address from ifconfig.me...")
    response = requests.get("https://ifconfig.me", timeout=5)
    return response.text


def get_local_ip():
    """Get the local IP address of the server."""
    # Attempt to connect to an Internet host in order to determine the local machine's IP address.
    try:
        # The IP address and port here are arbitrary and do not need to be reachable
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google's public DNS server
        local_ip = s.getsockname()[
            0
        ]  # getsockname returns a tuple (host, port)
        s.close()
    except Exception as e:  # pylint: disable=broad-except
        local_ip = "Unable to determine IP: " + str(e)

    return local_ip


def download_file(url, filename, destination) -> dict:
    """Download a file from a URL and save it to a location using requests."""
    log = False
    if log:
        logging.info(
            "Downloading file from %s to %s/%s...", url, destination, filename
        )

    try:
        with requests.get(url, stream=True, timeout=10) as r:
            r.raise_for_status()
            with open(os.path.join(destination, filename), "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    except requests.RequestException as e:
        logging.error("Failed to download file from %s: %s", url, e)
        return {
            "success": False,
            "message": f"Failed to download file from {url}: {e}",
        }

    # Verify that the file downloaded successfully
    if not os.path.exists(os.path.join(destination, filename)):
        logging.error("Request Complete but file does not exist")
        return {
            "success": False,
            "message": "Request Complete but file does not exist",
        }

    return {
        "success": True,
        "message": f"File downloaded from {url} to {destination}/{filename}",
    }
