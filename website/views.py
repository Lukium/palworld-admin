from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
)

from rcon import (
    rcon_connect,
    rcon_broadcast,
    rcon_fetch_players,
    rcon_kick_player,
    rcon_ban_player,
)

from installer import (
    check_install,
    install_server,
    first_run,
    run_server,
    update_palworld_settings_ini,
)

# from ui import close_browser, minimize_browser
import settings as s

default_values = s.default_values
descriptions = s.descriptions
default_settings_string = s.default_settings_string


def check_headers() -> dict:
    """Check the headers to determine if the request is coming from a WebView2 browser."""
    if "WebView2" in request.headers["Sec-Ch-Ua"]:
        webview_headers = {"webview": True}
    else:
        webview_headers = {"webview": False}
    return webview_headers


views = Blueprint("views", __name__)


# Define a simple route
@views.route("/")
def home():
    """Render the home page."""
    webview_headers = check_headers()
    return render_template("home.html", webview_headers=webview_headers)


@views.route("/loadrcon")
def loadrcon():
    """Render the RCON loader page."""
    webview_headers = check_headers()
    return render_template("rcon_loader.html", webview_headers=webview_headers)


@views.route("/rcon")
def rcon():
    """Render the RCON page."""
    webview_headers = check_headers()
    return render_template("rcon.html", webview_headers=webview_headers)


@views.route("/server-installer")
def server_installer():
    """Render the server installer page."""
    webview_headers = check_headers()
    return render_template(
        "server_installer.html", webview_headers=webview_headers
    )


@views.route("/server-installer-cmd", methods=["POST"])
def server_installer_cmd():
    """Run the server installer commands."""
    # Get the command from the form data
    data = request.json
    if data["function"] == "check_install":
        result = check_install()
    elif data["function"] == "install_server":
        result = install_server()
    elif data["function"] == "start_server":
        result = run_server(data["launcher"])
    elif data["function"] == "first_run":
        result = first_run()
    elif data["function"] == "update_settings":
        result = update_palworld_settings_ini(data["settings"])
    return jsonify(result)


@views.route("/settingsgen", methods=["GET", "POST"])
def settingsgen():
    """Render the settingsgen page."""
    webview_headers = check_headers()
    if request.method == "POST":
        # Construct the string from the form data
        settings = ["[/Script/Pal.PalGameWorldSettings]\nOptionSettings=("]
        for key in default_values.keys():
            value = request.form.get(key, default_values[key])
            settings.append(f"{key}={value},")
        settings_string = (
            "".join(settings)[:-1] + ")"
        )  # Remove last comma and close parenthesis

        return render_template(
            "settings_gen.html",
            defaults=default_values,
            descriptions=descriptions,
            settings_string=settings_string,
            webview_headers=webview_headers,
        )

    # Initial page load
    return render_template(
        "settings_gen.html",
        defaults=default_values,
        descriptions=descriptions,
        settings_string=default_settings_string,
        webview_headers=webview_headers,
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


@views.route("/close")
def close():
    """Close the webview browser window."""
    s.browser.close_browser()
    return "", 204


@views.route("/minimize")
def minimize():
    """Minimize the webview browser window."""
    s.browser.minimize_browser()
    return "", 204
