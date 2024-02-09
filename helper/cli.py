"""Command line interface for the application."""

import argparse


def parse_arguments():
    """Parse command line arguments."""
    result = {}
    parser = argparse.ArgumentParser(
        description="Launch the application with optional settings."
    )
    parser.add_argument(
        "-mp",
        "--ManagementPassword",
        type=str,
        help="""Set the management password for the Server Manager.
Must be at least 6 characters long.""",
    )
    parser.add_argument(
        "-r",
        "--Remote",
        action="store_true",
        default=False,
        help="Set the management mode of the Server Manager to remote.",
    )

    args = parser.parse_args()
    if args.ManagementPassword:
        result["ManagementPassword"] = args.ManagementPassword
    else:
        result["ManagementPassword"] = ""
    if args.Remote:
        result["Remote"] = "remote"
        if not args.ManagementPassword:
            raise ValueError(
                """You must set a management password when using remote mode.
Use the -mp flag to set the password."""
            )
        if len(args.ManagementPassword) < 6:
            raise ValueError(
                "The management password must be at least 6 characters long."
            )
    else:
        result["Remote"] = "local"
    return result


def parse_cli():
    """Parse command line arguments."""
    try:
        parsed_args = parse_arguments()
        return parsed_args
    except ValueError as e:
        print(f"Error: {e}")
        # Optionally, you can also provide guidance or next steps:
        print("Use -h for help.")
        # Exiting with a non-zero status code to indicate that an error occurred
        exit(1)
