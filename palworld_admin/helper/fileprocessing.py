"""File processing helper functions"""

import logging
import os
import zipfile


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


def extract_file(filelocation, filename, destination):
    """Use Zipfile to extract a file"""
    log = True
    result = {}
    # Check that the file location exists
    if not os.path.exists(filelocation):
        result["success"] = False
        result["message"] = "Location not found"
        logging.error("Location %s not found", filelocation)
        return result

    if not os.path.join(filelocation, filename):
        result["success"] = False
        result["message"] = "File not found"
        logging.error("File %s not found", filename)
        return result

    # Extract the file, creating the destination directory if it does not exist
    if not os.path.exists(destination):
        os.makedirs(destination)
        logging.info("Created directory %s", destination)

    # Ensure that the destination exists
    if not os.path.exists(destination):
        result["success"] = False
        result["message"] = "Destination not found"
        logging.error(
            "Destination %s not found and failed to be created", destination
        )
        return result

    # Extract the File to the destination
    try:
        with zipfile.ZipFile(
            os.path.join(filelocation, filename), "r"
        ) as zip_ref:
            zip_ref.extractall(destination)
            result["success"] = True
            result["message"] = f"File {filename} extracted to {destination}"
            if log:
                logging.info("File %s extracted to %s", filename, destination)
    except zipfile.BadZipFile as e:
        result["success"] = False
        result["message"] = f"Bad Zip File: {e}"
        logging.error("Bad Zip File: %s", e)
    except Exception as e:  # pylint: disable=broad-except
        result["success"] = False
        result["message"] = str(e)
        logging.error("Error extracting file %s", filename)
    return result
