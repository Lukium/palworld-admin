"""Helper functions for running OS commands."""

import logging
import subprocess


def detect_virtual_machine(operating_system: str) -> bool:
    """Detect if the server is running in a virtual machine."""
    result = {}
    log = False
    vm_models = [
        "VMware",
        "VirtualBox",
        "KVM",
        "Microsoft Virtual PC",
        "Hyper-V",
        "Xen",
        "Virtual Machine",
        "vServer",
        "Standard PC (Q35 + ICH9, 2009)",
    ]
    if log:
        logging.info("OS: %s", operating_system)
    if operating_system == "Windows":
        cmd = "(Get-WmiObject -Class Win32_ComputerSystem).Model"
        if log:
            logging.info("Detecting virtual machine: %s", cmd)

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            process = subprocess.run(
                ["powershell", cmd],
                capture_output=True,
                check=True,
                startupinfo=startupinfo,
                text=True,
            )
            output = process.stdout.strip()
            # Check if the output is in the VM models
            if output in vm_models:
                result["value"] = True
            # Check if any of the VM models are in the output
            # This is for when the model is not an exact match
            elif any(vm_model in output for vm_model in vm_models):
                result["value"] = True
            else:
                result["value"] = False
            if log:
                logging.info("Detecting virtual machine: %s", output)

            result["status"] = "success"
        except subprocess.CalledProcessError as e:
            result["status"] = "error"
            result["error"] = e
            logging.error("Error detecting virtual machine: %s", e)
    else:
        cmd = "systemd-detect-virt"

        if log:
            logging.info("Detecting virtual machine with: %s", cmd)

        try:
            process = subprocess.run(
                [cmd],
                capture_output=True,
                check=True,
                text=True,
            )
            output = process.stdout.strip().lower()

            if output == "none":
                result["value"] = False
            else:
                result["value"] = True

            if log:
                logging.info("Virtualization detected: %s", output)

            result["status"] = "success"
        except subprocess.CalledProcessError as e:
            result["status"] = "error"
            result["error"] = str(e)
            logging.error("Error detecting virtual machine: %s", e)
    return result
