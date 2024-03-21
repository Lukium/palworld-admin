""" The main module for the website. """

from datetime import datetime, timedelta
from functools import wraps
import io
import json
import logging
from mimetypes import guess_type
import os
import uuid
import shutil

# Must be included for pyinstaller to work
# from engineio.async_drivers import eventlet  # pylint: disable=unused-import
# import eventlet  # pylint: disable=unused-import disable=reimported

from flask_socketio import SocketIO

from flask import (
    Flask,
    Response,
    abort,
    jsonify,
    send_file,
    send_from_directory,
    redirect,
    url_for,
    flash,
    render_template,
    render_template_string,
    session,
    request,
)

from flask_openid_steam.flask_openid_steam import OpenID

from palworld_admin.rcon import (
    rcon_connect,
    resolve_address,
    rcon_fetch_players,
    rcon_broadcast,
    rcon_save,
    rcon_ban_player,
    rcon_kick_player,
    rcon_shutdown,
)

from palworld_admin.servermanager import (
    check_install,
    install_server,
    uninstall_server,
    run_server,
    check_server_running,
    backup_server,
    update_palworld_settings_ini,
    generate_world_option_save,
    install_ue4ss,
    install_palguard,
)

from palworld_admin.helper.dbmanagement import (
    get_stored_default_settings,
    commit_players_to_db,
    get_players_from_db,
    get_alembic_version,
)
from palworld_admin.settings import app_settings
from palworld_admin.converter.convert import convert_json_to_sav
from palworld_admin.classes import (
    db,
    AlembicVersion,
    LauncherSettings,
    RconSettings,
    Connection,
    Settings,
    Players,
)

DEFAULT_VALUES: dict = app_settings.palworldsettings_defaults.default_values
DESCRIPTIONS: dict = app_settings.palworldsettings_defaults.descriptions
DEFAULT_SETTINGS_STRING: str = (
    app_settings.palworldsettings_defaults.default_settings_string
)


def requires_auth(f):
    """Check if the user is authenticated. If not, redirect to the login page."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get(
            "authenticated"
        ):  # Checks if the user is not authenticated
            return redirect(
                url_for(
                    "login",
                    next=request.url,
                    management_mode=app_settings.localserver.management_mode,
                    version=app_settings.version,
                )
            )
        return f(*args, **kwargs)

    return decorated


def maybe_requires_auth(func):
    """Check if the management mode is set to remote and if so, require authentication."""
    if app_settings.localserver.management_mode == "remote":
        return requires_auth(func)
    else:
        return func


def initialize_database_defaults():
    """Initialize default records for the database."""
    # Check if AlembicVersion exists, if not, create a default record
    if not AlembicVersion.query.first():
        initial_alembic_version = AlembicVersion(
            version_num=app_settings.alembic_version
        )
        db.session.add(initial_alembic_version)
    db.session.commit()

    # Check if LauncherSettings exists, if not, create a default record
    if not LauncherSettings.query.first():
        initial_launcher_settings = LauncherSettings(
            launch_rcon=True,
            useperfthreads=True,
            NoAsyncLoadingThread=True,
            UseMultithreadForDS=True,
            query_port=27015,
            auto_backup=True,
            auto_backup_delay=3600,  # Default delay in seconds
            auto_backup_quantity=48,  # Default number of backups to keep
            publiclobby=False,
            auto_restart_triggers=True,
            auto_restart_on_unexpected_shutdown=True,
            ram_restart_trigger=0.0,  # Default RAM usage trigger for restart, in GB
        )
        db.session.add(initial_launcher_settings)

    # Commit here to ensure LauncherSettings exists before creating Settings
    db.session.commit()

    # Check if Connection exists, if not, create a default record
    if not Connection.query.first():
        initial_connection = Connection(
            name="Last Connection",
            host="127.0.0.1",
            port=25575,
            password="admin",
        )
        db.session.add(initial_connection)

    # Commit here to ensure Connection exists before creating RconSettings
    db.session.commit()

    # Ensure there's a RconSettings record linked to the default Connection
    if not RconSettings.query.first():
        connection = (
            Connection.query.first()
        )  # Assuming the first connection is the default
        initial_rcon_settings = RconSettings(connection_id=connection.id)
        db.session.add(initial_rcon_settings)

    # Commit here to ensure RconSettings exists before creating Settings
    db.session.commit()

    # Ensure there's a Settings record linking LauncherSettings and RconSettings
    if not Settings.query.first():
        launcher_settings = LauncherSettings.query.first()
        rcon_settings = RconSettings.query.first()
        initial_settings = Settings(
            launcher_settings_id=launcher_settings.id,
            rcon_settings_id=rcon_settings.id,
        )
        db.session.add(initial_settings)

    db.session.commit()


def flask_app():
    """Run the Flask app with socketio."""

    if app_settings.dev:
        app = Flask(__name__)
    else:
        app = Flask(__name__, static_folder=None)
        # Serve the templates from memory that were downloaded from the remote server
        app.jinja_loader = app_settings.memorystorage.template_loader

        # Serve the static files from memory that were downloaded from the remote server
        @app.route("/static/<path:filename>")
        def static(filename):
            """Serve static files from memory."""
            file_path = f"/static/{filename}"
            logging.info("Requested static file: %s", file_path)
            if file_path in app_settings.memorystorage.static_files_in_memory:
                content = app_settings.memorystorage.static_files_in_memory[
                    file_path
                ]
                # Use the mimetypes module to guess the correct MIME type
                mimetype, _ = guess_type(filename)
                mimetype = mimetype or "application/octet-stream"
                return Response(content, mimetype=mimetype)
            else:
                abort(404)

    # Set the secret key to a random UUID
    app.secret_key = uuid.uuid4().hex

    # Set the sqlite database URI and initialize the database
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f'sqlite:///{os.path.join(app_settings.exe_path,"palworld-admin.db")}'
    )

    db.init_app(app)

    with app.app_context():
        db.create_all()
        initialize_database_defaults()
        app_settings.localserver.all_players = get_players_from_db()
        app_settings.localserver.launcher_args = get_stored_default_settings(
            "LauncherSettings"
        )
        app_settings.localserver.rcon_last_connection_args = (
            get_stored_default_settings("Connection")
        )
        logging.info(
            "Last RCON Connection: %s",
            app_settings.localserver.rcon_last_connection_args,
        )
        alembic_version = get_alembic_version()

    if alembic_version:
        logging.info("Alembic DB Version: %s", alembic_version)

    @app.route("/restore-server-data", methods=["POST"])
    @maybe_requires_auth
    def restore_server_data():
        reply = {"command": "restore server data"}

        # Delete the existing server data directory recursively
        try:
            shutil.rmtree(app_settings.localserver.data_path)
        except FileNotFoundError:
            pass

        # Double check that the server data was deleted
        for _, dirs, files in os.walk(app_settings.localserver.data_path):
            if dirs or files:
                message = "Error: Failed to delete server data"
                reply["success"] = False
                reply["consoleMessage"] = message
                reply["outputMessage"] = message
                reply["toastMessage"] = message
                data = {"reply": reply, "success": False}
                return data
        logging.info("Server data deleted successfully")

        # Ensure the directory exists
        os.makedirs(app_settings.localserver.data_path, exist_ok=True)

        base_dir = os.path.dirname(app_settings.localserver.data_path)
        logging.info("Base Directory: %s", base_dir)

        # Save the uploaded files to the server data directory
        for file in request.files.getlist(
            "files[]"
        ):  # The file.filename contains the relative path due to how we set it in FormData
            # get the parent directory of the base_path

            relative_path = file.filename
            save_path = os.path.join(base_dir, relative_path)
            # logging.info("Save Path: %s", save_path)

            # Ensure the directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save the file
            file.save(save_path)

        logging.info("Server data restored successfully")

        # Verify the files were uploaded and processed successfully
        for file in request.files.getlist("files[]"):
            relative_path = file.filename
            save_path = os.path.join(base_dir, relative_path)
            if not os.path.exists(save_path):
                logging.info("Failed to restore: %s", relative_path)
                message = "Error: Failed to restore server data"
                reply["success"] = False
                reply["consoleMessage"] = message
                reply["outputMessage"] = message
                reply["toastMessage"] = message

                data = {"reply": reply, "success": False}
                logging.info("Reply: %s", data)
                return data

        ensured_paths = ["Saved/ImGui", "Saved/Logs"]
        # Ensure the required directories exist
        for ensured_path in ensured_paths:
            if not os.path.exists(os.path.join(base_dir, ensured_path)):
                os.makedirs(
                    os.path.join(base_dir, ensured_path), exist_ok=True
                )

        message = "Server data restored successfully"

        # Ensure correct OS Directory
        target_os = app_settings.app_os
        source_os_location = os.path.join(base_dir, "Saved", "Config")
        if (
            os.path.exists(os.path.join(source_os_location, "WindowsServer"))
            and target_os == "Linux"
        ):
            os.rename(
                os.path.join(source_os_location, "WindowsServer"),
                os.path.join(source_os_location, "LinuxServer"),
            )
            message = message + " and converted to Linux"
        elif (
            os.path.exists(os.path.join(source_os_location, "LinuxServer"))
            and target_os == "Windows"
        ):
            os.rename(
                os.path.join(source_os_location, "LinuxServer"),
                os.path.join(source_os_location, "WindowsServer"),
            )
            message = message + " and converted to Windows"

        reply["success"] = True
        reply["consoleMessage"] = message
        reply["outputMessage"] = message
        reply["toastMessage"] = message

        data = {"reply": reply, "success": True}

        logging.info("Reply: %s", data)

        return jsonify(data)

    @app.route("/", methods=["GET", "POST"])
    @maybe_requires_auth
    def main():
        """Render the home page."""
        if app_settings.dev_ui:
            template_to_render = "ui-test.html"
        else:
            if app_settings.supporter_build:
                template_to_render = "ui-supporter.html"
            else:
                template_to_render = "ui.html"

        return render_template(
            template_to_render,
            management_mode=app_settings.localserver.management_mode,
            version=app_settings.version,
            supporter_build=app_settings.supporter_build,
            supporter_version=app_settings.supporter_version,
            defaults=DEFAULT_VALUES,
            descriptions=DESCRIPTIONS,
        )

    @app.route("/query-db", methods=["POST"])
    @maybe_requires_auth
    def query_db():
        """Query the database."""
        log = True
        if log:
            logging.info("Querying the database. Data: %s", request.json)
        data = request.json
        if data["function"] == "get_default_settings":
            result = get_stored_default_settings(data["data"]["model"])
        return jsonify(result)

    # Route for shutting down the server
    # @app.route("/shutdown", methods=["POST"])
    # def shutdown():
    #     logging.info("Shutting down the server...")
    #     app_settings.shutdown_requested = True

    #     return "Server shutting down..."

    if app_settings.localserver.management_mode == "remote":

        @app.route("/login", methods=["GET", "POST"])
        def login():
            """Render the login page."""
            management_mode = session.get("management_mode", None)
            if request.method == "POST":
                if (
                    request.form["password"]
                    == app_settings.localserver.management_password
                ):
                    session["authenticated"] = True
                    return redirect(url_for("main"))
                else:
                    flash("Incorrect password. Please try again.")
            return render_template(
                "login.html",
                management_mode=management_mode,
                version=app_settings.version,
                supporter_build=app_settings.supporter_build,
                supporter_version=app_settings.supporter_version,
            )  # Ensure you have a login.html template

        @app.route("/logout")
        def logout():
            """Log the user out and redirect to the login page."""
            session.pop(
                "authenticated", None
            )  # Remove 'authenticated' from session
            return redirect(url_for("login"))

    @app.route("/favicon.ico")
    def favicon():
        """Serve the favicon."""
        return redirect(
            url_for("custom_static", filename="images/favicon.ico")
        )

    # Route for serving the resources directory
    @app.route("/resources/<path:filename>")
    def custom_static(filename):
        # if app_settings.pyinstaller_mode:
        #     directory = os.path.join(app_settings.meipass, "resources")
        #     return send_from_directory(directory, filename)
        return send_from_directory("resources", filename)

    @app.route("/generate_sav", methods=["POST"])
    def generate_sav():
        """Generate WorldOption.sav and return it as a file download."""
        # Generate WorldOption.sav.json and convert it to WorldOption.sav
        properties_data = {
            "Settings": {
                "struct_type": "PalOptionWorldSettings",
                "struct_id": "00000000-0000-0000-0000-000000000000",
                "id": None,
                "value": {},
                "type": "StructProperty",
            }
        }

        for (
            key,
            default_value,
        ) in app_settings.palworldsettings_defaults.default_values.items():
            submitted_value = request.form.get(key, default_value)
            if str(submitted_value) != str(default_value):
                if submitted_value.lower() in ["true", "false"]:
                    value = (
                        True if submitted_value.lower() == "true" else False
                    )
                    _type = "BoolProperty"
                elif submitted_value.replace(".", "", 1).isdigit():
                    value = (
                        float(submitted_value)
                        if "." in submitted_value
                        else int(submitted_value)
                    )
                    _type = (
                        "FloatProperty"
                        if "." in submitted_value
                        else "IntProperty"
                    )
                else:
                    value = submitted_value
                    _type = "StrProperty"

                properties_data["Settings"]["value"][key] = {
                    "id": None,
                    "value": value,
                    "type": _type,
                }

        json_data = {
            "header": app_settings.palworldsettings_defaults.worldoptionsav_json_data_header,
            "properties": {
                "Version": {"id": None, "value": 100, "type": "IntProperty"},
                "OptionWorldData": {
                    "struct_type": "PalOptionWorldSaveData",
                    "struct_id": "00000000-0000-0000-0000-000000000000",
                    "id": None,
                    "value": properties_data,
                    "type": "StructProperty",
                },
            },
            "trailer": "AAAAAA==",
        }

        # Save the JSON data to a file named 'WorldOption.sav.json'
        with open(
            os.path.join("./", "WorldOption.sav.json"), "w", encoding="utf-8"
        ) as json_file:
            json.dump(json_data, json_file, indent=2)

        # Check if WorldOption.sav exists and delete it
        if os.path.exists("WorldOption.sav"):
            os.remove("WorldOption.sav")

        # Run convert.py with the saved file as an argument
        # subprocess.run(["python3", "convert.py", "WorldOption.sav.json"])
        convert_json_to_sav("WorldOption.sav.json", "WorldOption.sav")

        # Load WorldOption.sav into memory
        with open("WorldOption.sav", "rb") as sav_file:
            sav_data = io.BytesIO(sav_file.read())

        # Delete the file from the filesystem
        os.remove("WorldOption.sav")
        os.remove("WorldOption.sav.json")

        # Set the filename for the file-like object
        sav_data.seek(0)
        return send_file(
            sav_data,
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name="WorldOption.sav",
        )

    tmp_dir = os.path.join(app_settings.exe_path, "tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    oid = OpenID(app, tmp_dir)
    openid_logger = logging.getLogger("openid")
    openid_logger.setLevel(logging.WARNING)

    @app.route("/steam-auth")
    @oid.loginhandler
    def steam_auth():
        # Get the IP address of the user connecting
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        session["client_ip"] = client_ip
        return oid.try_login(
            app_settings.steam_openid_url, ask_for=["nickname"]
        )

    @app.route("/steam-auth-complete")
    @oid.after_login
    def steam_auth_complete(resp):
        # Create a dict from the response
        steam_id = resp.identity_url.split("/")[-1]
        session["steam_id"] = steam_id
        # Check if the steamID is among the all_players list
        if steam_id not in [
            player["steam_id"]
            for player in app_settings.localserver.all_players
        ]:
            new_player = {
                "steam_id": steam_id,
                "steam_authenticated": True,
                "steam_auth_ip": session["client_ip"],
                "online": False,
                "name": None,
                "player_id": None,
                "save_id": None,
                "first_login": None,
                "last_seen": None,
                "whitelisted": False,
                "whitelisted_ip": "",
                "banned": False,
                "is_admin": False,
            }
            # Add the player to the all_players list
            app_settings.localserver.all_players.append(new_player)
        else:
            # Update the player's steam_authenticated status and IP
            for player in app_settings.localserver.all_players:
                if player["steam_id"] == steam_id:
                    player["steam_authenticated"] = True
                    player["steam_auth_ip"] = session["client_ip"]
        logging.info(
            "Player %s authenticated with SteamAuth using %s",
            steam_id,
            session["client_ip"],
        )
        # Commit the player to the database
        commit_players_to_db(app_settings.localserver.all_players)
        message = f"Steam ID: {steam_id} authenticated with with IP {session['client_ip']}"
        send_to_frontend(
            "update_players",
            {"success": True, "reply": {"player_auth": message}},
        )
        return render_template_string(
            "Login successful. Steam ID: {{steam_id}} authenticated with with IP {{IP}}",
            steam_id=steam_id,
            IP=session["client_ip"],
        )

    socketio = SocketIO(app, async_mode="eventlet")
    app_settings.localserver.socket = socketio

    def valid_value(value, expected_type):
        # Ensure the value is the expected type
        if expected_type == "port":
            # Ensure the value is an integer between 1 and 65535
            if not value.isdigit() or not 1 <= int(value) <= 65535:
                return False
        if expected_type == "password":
            # Ensure the value is a string between 1 and 64 characters
            if not 1 <= len(value) <= 64:
                return False
        return True

    def send_to_frontend(
        event, data, namespace: str = "/socket", room: str = None
    ):
        """Send data to the frontend."""
        socketio.emit(event, data, namespace=namespace, room=room)

    def process_frontend_command(
        func,
        *args,
        frontend_event: str = None,
        namespace: str = "/socket",
        **kwargs,
    ) -> None:
        """Process commands from the frontend.

        args:
            func: Function to run
            *args: Arguments to pass to the function
            reply_data: Data to send to the frontend
            frontend_event: Event to send to the frontend
            namespace: Namespace to use
            **kwargs: Keyword arguments to pass to the function

        returns:

        """
        indicator: dict = None
        if kwargs.get("indicator"):
            indicator = {"indicator": kwargs["indicator"]}
            kwargs.pop("indicator")

        try:
            reply = {"success": True, "reply": func(*args, **kwargs)}
            if "command" in reply["reply"]:
                reply["command"] = reply["reply"]["command"]
        except Exception as e:  # pylint: disable=broad-except
            reply = {
                "success": False,
                "reply": {
                    "consoleMessage": f"Error: {e}",
                    "outputMessage": f"Error: {e}",
                    "toastMessage": f"Error: {e}",
                },
            }
            if "command" in reply["reply"]:
                reply["command"] = reply["reply"]["command"]

        if indicator:
            socketio.emit(
                "stop_indicator",
                indicator,
                namespace="/socket",
            )

        if frontend_event:
            send_to_frontend(
                frontend_event,
                reply,
                namespace=namespace,
            )
            return

        return reply

    @socketio.on("connected", namespace="/socket")
    def socket_connected():
        def func():
            app_settings.current_client = request.sid
            logging.info("Client connected to socket: %s", request.sid)
            reply = {
                "command": "socket connect",
                "success": True,
            }

            return reply

        return process_frontend_command(func)

    @socketio.on("disconnect", namespace="/socket")
    def socket_disconnect():
        def func():
            logging.info(
                "Client disconnected from socket: %s",
                app_settings.current_client,
            )
            app_settings.current_client = None

        process_frontend_command(func)

    ############# RCON SOCKET EVENTS #############

    @socketio.on("connect_rcon", namespace="/socket")
    def connect_rcon(data):

        def func(data):
            host = resolve_address(data.get("host"))
            port = data.get("port")
            password = data.get("password")
            if "Error" in host:
                return {"toastMessage": host}

            if not valid_value(port, "port"):
                return {"toastMessage": "Invalid port number"}

            if not valid_value(password, "password"):
                return {"toastMessage": "Invalid password"}

            message = rcon_connect(host, port, password)

            reply = {
                "command": "rcon connect",
                "consoleMessage": message["message"],
                "outputMessage": message["message"],
                "toastMessage": message["message"],
            }

            if message["status"] == "error":
                reply["success"] = False
                reply["vars"] = {
                    "rconConnected": False,
                    "serverName": "",
                    "serverVersion": "",
                }
                return reply

            app_settings.localserver.connected = True
            app_settings.localserver.ip = host
            app_settings.localserver.port = port
            app_settings.localserver.password = password
            reply["success"] = True
            reply["vars"] = {
                "rconConnected": True,
                "serverName": message["server_name"],
                "serverVersion": message["server_version"],
            }

            if "palguard_commands" in message:
                reply["vars"]["palguardCommands"] = message[
                    "palguard_commands"
                ]

            # logging.info("Reply: %s", reply)
            return reply

        return process_frontend_command(func, data)

    @socketio.on("disconnect_rcon", namespace="/socket")
    def disconnect_rcon():
        def func():
            app_settings.localserver.connected = False
            app_settings.localserver.ip = ""
            app_settings.localserver.port = 0
            app_settings.localserver.password = ""
            reply = {
                "command": "rcon disconnect",
                "success": True,
                "vars": {
                    "rconConnected": False,
                    "serverName": "",
                    "serverVersion": "",
                    "playerCount": "",
                },
                "consoleMessage": "RCON disconnected",
                "outputMessage": "RCON disconnected",
                "toastMessage": "RCON disconnected",
            }

            return reply

        return process_frontend_command(func)

    @socketio.on("rcon_broadcast", namespace="/socket")
    def rcon_breadcast_socket(data):
        def func(data):
            message = rcon_broadcast(
                app_settings.localserver.ip,
                app_settings.localserver.port,
                app_settings.localserver.password,
                data["message"],
                data["broadcastOrCommand"],
            )
            # logging.info("RCON Broadcast Message Result: %s", message)
            reply = {
                "command": "rcon broadcast",
                "consoleMessage": message["message"],
                "outputMessage": message["message"],
                "toastMessage": message["message"],
            }
            return reply

        return process_frontend_command(func, data)

    @socketio.on("rcon_save", namespace="/socket")
    def rcon_save_socket():
        def func():
            message = rcon_save(
                app_settings.localserver.ip,
                app_settings.localserver.port,
                app_settings.localserver.password,
            )
            reply = {
                "command": "rcon save",
                "success": message["status"] == "success",
                "consoleMessage": message["message"],
                "outputMessage": message["message"],
                "toastMessage": message["message"],
            }
            return reply

        return process_frontend_command(func)

    @socketio.on("rcon_shutdown", namespace="/socket")
    def rcon_shutdown_socket(data):
        def func(data):
            app_settings.localserver.shutting_down = True
            message = rcon_shutdown(
                app_settings.localserver.ip,
                app_settings.localserver.port,
                app_settings.localserver.password,
                data["delay"],
                data["message"],
            )
            logging.info("RCON Shutdown Message: %s", message)
            reply = {
                "command": "rcon shutdown",
                "success": message["status"] == "success",
                "time_to_shutdown": data["delay"],
                "vars": {
                    "expectedToBeRunning": False,
                },
                "consoleMessage": message["message"],
                "outputMessage": message["message"],
                "toastMessage": message["message"],
            }

            if "restarting" in data:
                if data["restarting"]:
                    app_settings.localserver.restarting = True

            app_settings.localserver.expected_to_be_running = False
            app_settings.localserver.shutting_down = False
            return reply

        return process_frontend_command(func, data)

    @socketio.on("rcon_kick_ban", namespace="/socket")
    def rcon_kick_ban_player(data):
        def func(data):
            if data["action"] == "kick":
                message = rcon_kick_player(
                    app_settings.localserver.ip,
                    app_settings.localserver.port,
                    app_settings.localserver.password,
                    data["steamid"],
                )
            elif data["action"] == "ban":
                message = rcon_ban_player(
                    app_settings.localserver.ip,
                    app_settings.localserver.port,
                    app_settings.localserver.password,
                    data["steamid"],
                )
            reply = {
                "command": f"rcon {data['action']}",
                "consoleMessage": f'{message["message"]} - {data["playerName"]}',
                "outputMessage": f'{message["message"]} - {data["playerName"]}',
                "toastMessage": f'{message["message"]} - {data["playerName"]}',
            }
            return reply

        return process_frontend_command(func, data)

    ############# END RCON SOCKET EVENTS #############

    ############# SERVER MANAGER SOCKET EVENTS #############

    @socketio.on("check_install", namespace="/socket")
    def check_install_socket():
        def func():
            result = check_install()
            # logging.info("Check Install Result: %s", result)

            if result["status"] == "success":
                reply = {
                    "command": "check install",
                    "success": True,
                    "vars": {
                        "os": result["os"]["value"],
                        "steamcmdInstalled": result["steamcmd"]["value"],
                        "palserverInstalled": result["palserver"]["value"],
                    },
                }
                if "settings" in result:
                    reply["vars"]["serverSettings"] = result["settings"]
                if "world_options_sav" in result:
                    reply["vars"]["worldOptionSavExists"] = result[
                        "world_options_sav"
                    ]["value"]
                if (
                    app_settings.localserver.installing
                    and result["palserver"]["value"]
                ):
                    reply["outputMessage"] = "Server installation complete"
                    reply["toastMessage"] = "Server installation complete"
                    app_settings.localserver.installing = False
            return reply

        return process_frontend_command(
            func, frontend_event="check_install", indicator="IO"
        )

    @socketio.on("install_server", namespace="/socket")
    def install_server_socket():
        def func():
            app_settings.localserver.installing = True
            result = install_server()
            # logging.info("Result: %s", result)

            message = result["message"]
            reply = {
                "command": "install server",
                "success": result["status"] == "success",
                "consoleMessage": message,
                # "outputMessage": message,
                "toastMessage": message,
            }

            result = check_install()

            if result["status"] == "success":
                reply["vars"] = {
                    "os": result["os"]["value"],
                    "steamcmdInstalled": result["steamcmd"]["value"],
                    "palserverInstalled": result["palserver"]["value"],
                }

            # app_settings.localserver.installing = False

            return reply

        return process_frontend_command(
            func, frontend_event="install_server", indicator="IO"
        )

    @socketio.on("launch_server", namespace="/socket")
    def start_server_socket(data):
        def func(data):
            result = run_server(launcher_args=data)
            logging.info("Launch Server Result: %s", result)

            message = result["message"]
            reply = {
                "command": "launch server",
                "success": result["status"] == "success",
                "outputMessage": message,
                "toastMessage": message,
            }
            if result["status"] == "success":
                reply["vars"] = {
                    "expectedToBeRunning": True,
                    "launcherArgs": data,
                }
                ### Auto Backup ###
                app_settings.localserver.run_auto_backup = data["auto_backup"]
                app_settings.localserver.backup_interval = data[
                    "auto_backup_delay"
                ]
                app_settings.localserver.backup_retain_count = data[
                    "auto_backup_quantity"
                ]
                backup_server_socket(
                    {
                        "backup_type": "launch",
                        "backup_count": data["auto_backup_quantity"],
                    }
                )

                # If the server is restarting, set the restarting variable to False
                if app_settings.localserver.restarting:
                    app_settings.localserver.restarting = False

                app_settings.localserver.running = True
                app_settings.localserver.expected_to_be_running = True
                app_settings.localserver.last_launcher_args = data

                check_server_running_socket()

            return reply

        return process_frontend_command(
            func, data, frontend_event="launch_server", indicator="UP"
        )

    @socketio.on("check_server_running", namespace="/socket")
    def check_server_running_socket():
        def func():
            reply = {}
            result = check_server_running()
            # logging.info("Result: %s", result)

            launcher_args = app_settings.localserver.launcher_args

            if result["value"] is False:
                app_settings.localserver.running = False

            # If the server is not running and it's expected to be running,
            # And no client is connected to backend, restart the server
            if (
                not app_settings.localserver.running
                and app_settings.localserver.expected_to_be_running
                and app_settings.localserver.launcher_args[
                    "auto_restart_on_unexpected_shutdown"
                ]
                and app_settings.localserver.launcher_args[
                    "auto_restart_triggers"
                ]
                and app_settings.current_client is None
            ):
                logging.info(
                    "Server stopped, and there's no client to restart it. Restarting Server..."
                )
                with app.app_context():
                    run_server(launcher_args=launcher_args)
                return

            # If this is the first check, set the expected_to_be_running variable
            if (
                app_settings.localserver.running_check_count == 0
                and result["status"] == "success"
                and result["value"] is True
            ):
                logging.info(
                    "Launcher Args: %s", app_settings.localserver.launcher_args
                )
                app_settings.localserver.steam_auth = (
                    app_settings.localserver.launcher_args.get("steam_auth")
                )
                app_settings.localserver.enforce_steam_auth_ip = (
                    app_settings.localserver.launcher_args.get(
                        "enforce_steam_auth_ip"
                    )
                )
                app_settings.localserver.expected_to_be_running = True
                reply["vars"] = {}
                reply["vars"]["expectedToBeRunning"] = True
                reply["outputMessage"] = (
                    "Server Running on Startup, Starting Monitoring..."
                )

            reply["command"] = "check server running"
            reply["success"] = result["status"] == "success"
            reply["vars"] = {
                "launcherArgs": app_settings.localserver.launcher_args,
                "expectedToBeRunning": app_settings.localserver.expected_to_be_running,
                "serverRunning": result["value"],
                "runningCheckCount": app_settings.localserver.running_check_count,
                "cpuUsage": result["cpu_usage"],
                "ramUsage": result["ram_usage"],
            }

            app_settings.localserver.last_cpu_usage = result["cpu_usage"]
            app_settings.localserver.last_ram_usage = result["ram_usage"]

            # If the server is shutting down and the check returns False,
            # reset the shutting_down variable
            if (
                app_settings.localserver.shutting_down
                and result["value"] is False
            ):
                app_settings.localserver.shutting_down = False
                app_settings.localserver.expected_to_be_running = False
                reply["vars"]["expectedToBeRunning"] = False
                reply["outputMessage"] = "Server has been shut down"

            app_settings.localserver.running_check_count += 1
            reply["success"] = result["status"] == "success"
            # logging.info("Check Server Running Reply: %s", reply)
            return reply

        # If restarting, reply to the frontend where the request came from
        if app_settings.localserver.restarting:
            return process_frontend_command(func, indicator="IO")

        # If not restarting, reply to check_server_running_socket
        return process_frontend_command(
            func, frontend_event="check_server_running", indicator="UP"
        )

    @socketio.on("backup_server", namespace="/socket")
    def backup_server_socket(data):
        def func(data):
            result = backup_server(data)
            logging.info("Backup Server Result: %s", result)

            message = result["message"]
            reply = {
                "command": "backup server",
                "success": result["status"] == "success",
                "outputMessage": message,
                "toastMessage": message,
            }
            if result["status"] == "success":
                app_settings.localserver.last_backup = datetime.now()
                reply["vars"] = {
                    "lastBackup": app_settings.localserver.last_backup.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                }
            return reply

        # If restarting, reply to the frontend where the request came from
        if app_settings.localserver.restarting:
            return process_frontend_command(func, data, indicator="IO")

        # If not restarting, reply to backup_server_socket
        return process_frontend_command(
            func, data, frontend_event="backup_server", indicator="IO"
        )

    @socketio.on("store_server_settings", namespace="/socket")
    def store_server_settings(data):
        def func(data):
            result = update_palworld_settings_ini(data)
            logging.info("Update Server Settings Result: %s", result)

            message = ""
            reply = {
                "command": "update server settings",
                "ini_success": result["status"] == "success",
            }
            if result["status"] == "success":
                result = generate_world_option_save(data)
                reply["sav_success"] = result["success"]

                if result["success"]:
                    message = "PalWorldSettings.ini and WorldOption.sav updated successfully"
                    result = check_install()
                    if result["status"] == "success":
                        reply["vars"] = {
                            "serverSettings": result["settings"],
                            "worldOptionSavExists": result[
                                "world_options_sav"
                            ]["value"],
                        }
                else:
                    message = (
                        "PalWorldSettings.ini updated successfully, "
                        + "but WorldOption.sav failed to update"
                    )
            else:
                message = (
                    "Failed to update PalWorldSettings.ini and WorldOption.sav"
                )

            reply["consoleMessage"] = message
            reply["outputMessage"] = message
            reply["toastMessage"] = message

            return reply

        return process_frontend_command(func, data, indicator="IO")

    @socketio.on("delete_world_option", namespace="/socket")
    def delete_world_option():
        def func():
            reply = {"command": "delete world option"}
            target_file = os.path.join(
                app_settings.localserver.sav_path, "WorldOption.sav"
            )
            try:
                message = "WorldOption.sav deleted successfully"
                success = True

                os.remove(target_file)
                if os.path.exists(target_file):
                    message = "Failed to delete WorldOption.sav"
                    success = False

                result = check_install()
                if result["status"] == "success":
                    reply["vars"] = {
                        "serverSettings": result["settings"],
                        "worldOptionSavExists": result["world_options_sav"][
                            "value"
                        ],
                    }

            except Exception as e:  # pylint: disable=broad-except
                message = f"Error: {e}"
                success = False

            reply["consoleMessage"] = message
            reply["outputMessage"] = message
            reply["toastMessage"] = message
            reply["success"] = success

            return reply

        return process_frontend_command(func, indicator="IO")

    @socketio.on("uninstall_server", namespace="/socket")
    def uninstall_server_socket():
        def func():
            result = uninstall_server()
            logging.info("Uninstall Server Result: %s", result)

            message = result["message"]
            reply = {
                "command": "uninstall server",
                "success": result["status"] == "success",
                "consoleMessage": message,
                "outputMessage": message,
                "toastMessage": message,
            }

            if result["status"] == "success":
                app_settings.localserver.installing = False
                app_settings.localserver.running = False
                app_settings.localserver.expected_to_be_running = False
                app_settings.localserver.connected = False
                app_settings.localserver.ip = ""
                app_settings.localserver.port = 0
                app_settings.localserver.password = ""
                app_settings.localserver.shutting_down = False
                app_settings.localserver.restarting = False
                app_settings.localserver.last_launcher_args = None
                app_settings.localserver.last_backup = None
                app_settings.localserver.run_auto_backup = False
                app_settings.localserver.backup_interval = 0
                app_settings.localserver.backup_retain_count = 0
                app_settings.localserver.last_backup = None
                app_settings.localserver.last_cpu_usage = 0
                app_settings.localserver.last_ram_usage = 0
                app_settings.localserver.running_check_count = 0
                app_settings.localserver.rcon_monitoring_connection_error_count = (
                    0
                )

            return reply

        return process_frontend_command(func, indicator="IO")

    @socketio.on("install_ue4ss", namespace="/socket")
    def install_UE4SS_socket():
        """Install UE4SS Socket Event."""

        def func():
            result = install_ue4ss()
            logging.info("Install UE4SS Result: %s", result)

            message = result["message"]
            reply = {
                "command": "Install UE4SS",
                "success": result["status"] == "success",
                "outputMessage": message,
            }

            return reply

        return process_frontend_command(func, indicator="IO")

    @socketio.on("install_palguard", namespace="/socket")
    def install_palguard_socket(data):
        """Install PalGuard Socket Event."""

        def func(data):
            result = install_palguard(data)
            logging.info("Install PalGuard Result: %s", result)

            message = result["message"]
            reply = {
                "command": "Install PalGuard",
                "success": result["success"],
                "outputMessage": message,
            }

            return reply

        return process_frontend_command(func, data, indicator="IO")

    ############# END SERVER MANAGER SOCKET EVENTS #############

    ############# SERVER MONITOR #############

    def server_minitor_task():
        timer = 0
        up_indicator = False
        rcon_indicator = False
        backup_indicator = False

        def rcon_monitor():
            reply = {"command": "rcon monitor", "success": False}
            error_count = (
                app_settings.localserver.rcon_monitoring_connection_error_count
            )
            result = rcon_fetch_players(
                app_settings.localserver.ip,
                app_settings.localserver.port,
                app_settings.localserver.password,
            )
            # logging.info("RCON Monitor Result: %s", result)
            if result["status"] == "success":
                app_settings.localserver.rcon_monitoring_connection_error_count = (
                    0
                )

                reply["success"] = True
                reply["vars"] = {
                    "rconConnected": True,
                    "playerCount": result["player_count"],
                }
                reply["players"] = result["players"]
                if "players_left" in result:
                    reply["players_left"] = result["players_left"]
                if "players_joined" in result:
                    reply["players_joined"] = result["players_joined"]
                    # logging.info(
                    #     "Players Joined: %s", result["players_joined"]
                    # )
                if "auto_kicked_players" in result:
                    reply["auto_kicked_players"] = result[
                        "auto_kicked_players"
                    ]
            else:
                logging.info("RCON Monitor Error: %s", result["message"])
                app_settings.localserver.rcon_monitoring_connection_error_count += (
                    1
                )
                if (
                    result["message"]
                    == "Connection Error: [winerror 10061] no connection could be made because the target machine actively refused it"  # pylint: disable=line-too-long
                    or result["message"]
                    == "Connection Error: [errno 111] connection refused"  # Linux
                    or result["message"]
                    == "Connection Error: [errno 104] connection reset by peer"  # Wine
                ):
                    if error_count > 2:
                        app_settings.localserver.rcon_monitoring_connection_error_count = (
                            0
                        )
                        reply = {
                            "command": "rcon monitor",
                            "success": False,
                            "players": [],
                            "vars": {
                                "serverName": "",
                                "serverVersion": "",
                                "playerCount": "",
                            },
                            "consoleMessage": "Server appears to be offline. Disconnecting from RCON.",  # pylint: disable=line-too-long
                            "toastMessage": "Server appears to be offline. Disconnecting from RCON.",  # pylint: disable=line-too-long
                            "outputMessage": "Server appears to be offline. Disconnecting from RCON.",  # pylint: disable=line-too-long
                        }
                    else:
                        message = f"RCON Connection Error: Server actively refused the connection {error_count+1}/3"  # pylint: disable=line-too-long
                        reply = {
                            "command": "rcon monitor",
                            "success": False,
                            "players": [],
                            "vars": {
                                "serverName": "",
                                "serverVersion": "",
                                "playerCount": "",
                            },
                            "outputMessage": message,
                            "consoleMessage": message,
                        }

            return reply

        def start_indicator(indicator):
            socketio.emit(
                "start_indicator",
                {"indicator": indicator},
                namespace="/socket",
            )

        while True:
            server_running = app_settings.localserver.running
            rcon_connected = app_settings.localserver.connected
            rcon_interval = app_settings.localserver.rcon_monitoring_interval
            server_monitor_interval = (
                app_settings.localserver.server_monitoring_interval
            )
            player_to_db_interval = (
                app_settings.localserver.player_commit_to_db_interval
            )

            # Auto Backups
            if app_settings.localserver.run_auto_backup:
                backup_interval = float(
                    app_settings.localserver.backup_interval
                )
                backup_count = app_settings.localserver.backup_retain_count
                last_backup = app_settings.localserver.last_backup
                if last_backup is None:
                    last_backup = datetime.now()
                next_backup = last_backup + timedelta(seconds=backup_interval)

                if backup_indicator:
                    backup_indicator = False
                    backup_server_socket(
                        {
                            "backup_type": "automatic",
                            "backup_count": backup_count,
                        }
                    )
                    next_backup = datetime.now() + timedelta(
                        seconds=backup_interval
                    )

                if datetime.now() > next_backup and server_running:
                    backup_indicator = True
                    start_indicator("IO")

            if rcon_indicator:
                rcon_indicator = False
                process_frontend_command(
                    rcon_monitor,
                    frontend_event="update_players",
                    indicator="RCON",
                )

            # Fetch the players from the server every rcon_interval seconds if connected
            if (
                rcon_connected
                and timer % rcon_interval == 0
                and app_settings.localserver.shutting_down is False
            ):
                start_indicator("RCON")
                rcon_indicator = True

            # Check server running every server_monitor_interval seconds
            if up_indicator:
                up_indicator = False
                check_server_running_socket()

            if (
                app_settings.localserver.expected_to_be_running
                and timer % server_monitor_interval == 0
            ):
                start_indicator("UP")
                up_indicator = True

            # Commit players to the database every player_to_db_interval seconds
            if timer % player_to_db_interval == 0:
                if len(app_settings.localserver.all_players) > 0:
                    with app.app_context():
                        commit_players_to_db(
                            app_settings.localserver.all_players
                        )

            timer += 0.5
            # logging.info("Server Monitor Timer: %s", timer)
            # Use socketio.sleep for proper thread management
            socketio.sleep(0.5)

    check_install()
    # Start the server from the CLI if the settings are set
    if (
        app_settings.cli_launch_server
        and app_settings.localserver.palserver_installed
        and app_settings.localserver.launcher_args is not {}
        and app_settings.localserver.rcon_last_connection_args is not {}
    ):

        def task__launch_server_from_cli():
            """Launch the server from the CLI."""
            socketio.sleep(5)
            with app.app_context():
                launcher_args = app_settings.localserver.launcher_args
                launcher_args["rcon_port"] = (
                    app_settings.localserver.rcon_last_connection_args["port"]
                )
                launcher_args["public_port"] = (
                    app_settings.localserver.server_settings["PublicPort"]
                )

                run_server(launcher_args=launcher_args)
                app_settings.localserver.running = True
                app_settings.localserver.expected_to_be_running = True

        # Start the server from the CLI
        socketio.start_background_task(task__launch_server_from_cli)

    # Start the server monitor in the background
    socketio.start_background_task(server_minitor_task)

    # Set socketIO to use the Flask app
    logging.info("Launching application on port %s", app_settings.app_port)
    socketio.run(app, host="0.0.0.0", port=app_settings.app_port, debug=False)

    return app
