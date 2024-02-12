"""Define the routes for the website."""

from functools import wraps
import logging

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    url_for,
    redirect,
    session,
)

from rcon import (
    rcon_connect,
    rcon_broadcast,
    rcon_fetch_players,
    rcon_kick_player,
    rcon_ban_player,
    rcon_save,
    rcon_shutdown,
)

from servermanager.local import (
    check_install,
    install_server,
    backup_server,
    first_run,
    run_server,
    update_palworld_settings_ini,
    check_server_running,
)

from settings import app_settings

DEFAULT_VALUES: dict = app_settings.palworldsettings_defaults.default_values
DESCRIPTIONS: dict = app_settings.palworldsettings_defaults.descriptions
DEFAULT_SETTINGS_STRING: str = (
    app_settings.palworldsettings_defaults.default_settings_string
)


def check_headers() -> dict:
    """Check the headers to determine if the request is coming from a WebView2 browser."""
    if "Sec-Ch-Ua" in request.headers:
        if "WebView2" in request.headers["Sec-Ch-Ua"]:
            webview_headers = {"webview": True}
        else:
            webview_headers = {"webview": False}
        return webview_headers
    else:
        return {"webview": False}


def go_to(url: str):
    """Open the webview browser window to the specified URL."""
    headers = check_headers()
    # Insert headers and management mode into the session
    session["webview_headers"] = headers
    session["management_mode"] = app_settings.localserver.management_mode

    if app_settings.dev:
        return render_template(
            url,
            webview_headers=headers,
            management_mode=app_settings.localserver.management_mode,
            version=app_settings.version,
        )
    else:
        if headers["webview"]:
            return render_template(
                url,
                webview_headers=headers,
                management_mode=app_settings.localserver.management_mode,
                version=app_settings.version,
            )
        else:
            return render_template(
                url,
                webview_headers=headers,
                management_mode=app_settings.localserver.management_mode,
                version=app_settings.version,
            )
            # return jsonify({"status": "error", "message": "Permission denied"})


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
                    webview_headers=check_headers(),
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


def create_views():
    """Create the views blueprint."""

    views = Blueprint("views", __name__)

    @views.route("/", methods=["GET", "POST"])
    def main():
        """Render the home page."""
        return go_to("main.html")

    @views.route("/home")
    def home():
        """Render the main page."""
        return go_to("home.html")

    @views.route("/server-installer")
    @maybe_requires_auth
    def server_installer():
        """Render the server installer page."""
        return go_to("server_installer.html")

    @views.route("/server-installer-cmd", methods=["POST"])
    @maybe_requires_auth
    def server_installer_cmd():
        """Run the server installer commands."""
        # Get the command from the form data
        data = request.json
        if data["function"] == "check_install":
            result = check_install()
        elif data["function"] == "install_server":
            result = install_server()
        elif data["function"] == "backup_server":
            result = backup_server(data["data"])
        elif data["function"] == "start_server":
            result = run_server(data["data"])
        elif data["function"] == "first_run":
            result = first_run()
        elif data["function"] == "update_settings":
            logging.info("Data: %s", data)
            result = update_palworld_settings_ini(data["data"])
        elif data["function"] == "check_server_running":
            result = check_server_running()
        return jsonify(result)

    @views.route("/rcon")
    def rcon():
        """Render the RCON page."""
        return go_to("rcon.html")

    @views.route("/settingsgen", methods=["GET", "POST"])
    def settingsgen():
        """Render the settingsgen page."""
        webview_headers = check_headers()
        if request.method == "POST":
            # Construct the string from the form data
            settings = ["[/Script/Pal.PalGameWorldSettings]\nOptionSettings=("]
            for (
                key
            ) in (
                DEFAULT_VALUES.keys()  # pylint: disable=consider-iterating-dictionary
            ):
                value = request.form.get(key, DEFAULT_VALUES[key])
                settings.append(f"{key}={value},")
            settings_string = (
                "".join(settings)[:-1] + ")"
            )  # Remove last comma and close parenthesis

            logging.info("Settings String: %s", settings_string)

            return render_template(
                "settings_gen.html",
                defaults=DEFAULT_VALUES,
                descriptions=DESCRIPTIONS,
                settings_string=settings_string,
                webview_headers=webview_headers,
                version=app_settings.version,
            )

        # Initial page load
        return render_template(
            "settings_gen.html",
            defaults=DEFAULT_VALUES,
            descriptions=DESCRIPTIONS,
            settings_string=DEFAULT_SETTINGS_STRING,
            webview_headers=webview_headers,
            version=app_settings.version,
        )

    @views.route("/connect", methods=["POST"])
    def connect():
        """Connect to the RCON server."""
        data = request.json
        ip_address = data["ip"]
        port = data["port"]
        password = data["password"]

        result = rcon_connect(ip_address, port, password)
        return jsonify(result)

    @views.route("/broadcast", methods=["POST"])
    def broadcast():
        """Broadcast a message to the server."""
        data = request.json
        ip_address = data["ip"]
        port = data["port"]
        password = data["password"]
        message = data["message"]

        result = rcon_broadcast(ip_address, port, password, message)
        return jsonify(result)

    @views.route("/getplayers", methods=["POST"])
    def getplayers():
        """Get the list of players on the server."""
        data = request.json
        ip_address = data["ip"]
        port = data["port"]
        password = data["password"]

        result = rcon_fetch_players(ip_address, port, password)
        return jsonify(result)

    @views.route("/kickplayer", methods=["POST"])
    def kickplayer():
        """Kick a player from the server."""
        data = request.json
        ip_address = data["ip"]
        port = data["port"]
        password = data["password"]
        player_steamid = data["player_steamid"]

        result = rcon_kick_player(ip_address, port, password, player_steamid)
        return jsonify(result)

    @views.route("/banplayer", methods=["POST"])
    def banplayer():
        """Ban a player from the server."""
        data = request.json
        ip_address = data["ip"]
        port = data["port"]
        password = data["password"]
        player_steamid = data["player_steamid"]

        result = rcon_ban_player(ip_address, port, password, player_steamid)
        return jsonify(result)

    @views.route("/save", methods=["POST"])
    def save():
        """Save current game state."""
        data = request.json
        ip_address = data["ip"]
        port = data["port"]
        password = data["password"]

        result = rcon_save(ip_address, port, password)
        return jsonify(result)

    @views.route("/shutdown", methods=["POST"])
    def shutdown():
        """Shutdown the server."""
        data = request.json
        ip_address = data["ip"]
        port = data["port"]
        password = data["password"]
        delay = data["delay"]
        message = data["message"]

        result = rcon_shutdown(ip_address, port, password, delay, message)
        return jsonify(result)

    @views.route("/close")
    def close():
        """Close the webview browser window."""
        app_settings.main_ui.close_browser()
        return "", 204

    @views.route("/minimize")
    def minimize():
        """Minimize the webview browser window."""
        app_settings.main_ui.minimize_browser()
        return "", 204

    return views
