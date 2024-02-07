"""File processing helper functions"""

import logging
import os


def file_to_lines(filename):
    """Read a file and return the lines as a list of strings"""
    result = {}
    if os.path.isfile(filename):
        logging.info("Found %s, reading...", filename)
        try:
            with open(filename, "r", encoding="utf-8") as f:
                lines = f.readlines()
                result["status"] = "success"
                result["lines"] = lines
                logging.info("Read %s lines", len(lines))
        except Exception as e:  # pylint: disable=broad-except
            result["status"] = "error"
            result["message"] = str(e)
            logging.error("Error reading file %s", filename)
    else:
        result["status"] = "error"
        result["message"] = "File not found"
        logging.error("File not found %s", filename)
    return result
