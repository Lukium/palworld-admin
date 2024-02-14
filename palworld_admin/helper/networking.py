"""This module contains helper functions for networking tasks."""

import logging
import socket

import requests


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
