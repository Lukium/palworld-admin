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
        "--management-password",
        type=str,
        default="",
        help="""Set the management password for the Server Manager.
Must be at least 6 characters long.""",
    )
    parser.add_argument(
        "-r",
        "--remote",
        action="store_true",
        default=False,
        help="Set the management mode of the Server Manager to remote.",
    )

    parser.add_argument(
        "-nui",
        "--no-user-interface",
        action="store_true",
        default=False,
        help="Start the application without the user interface.",
    )

    parser.add_argument(
        "-nc",
        "--no-console",
        action="store_true",
        default=False,
        help="Start the application without the console.",
    )

    parser.add_argument(
        "-mdb",
        "--migrate-database",
        default=False,
        action="store_true",
        help="Migrate the database to the latest version.",
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8210,
        help="Set the port for the webserver to listen on.",
        action="store",
    )

    parser.add_argument(
        "-ls",
        "--launch-server",
        action="store_true",
        default=False,
        help="Launch the server immediately.",
    )

    args = parser.parse_args()
    if args.management_password:
        result["ManagementPassword"] = args.management_password
    else:
        result["ManagementPassword"] = ""
    if args.remote:
        result["Remote"] = "remote"
        if not args.management_password:
            raise ValueError(
                """You must set a management password when using remote mode.
Use the -mp flag to set the password."""
            )
        if len(args.management_password) < 6:
            raise ValueError(
                "The management password must be at least 6 characters long."
            )
    else:
        result["Remote"] = "local"

    if args.launch_server:
        result["LaunchServer"] = True
    else:
        result["LaunchServer"] = False
    result["MigrateDatabase"] = args.migrate_database
    result["NoUserInterface"] = args.no_user_interface
    result["NoConsole"] = args.no_console
    result["Port"] = args.port
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
