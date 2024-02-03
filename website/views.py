from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
)

from rcon import (
    rcon_connect,
    rcon_broadcast,
    rcon_fetch_players,
    rcon_kick_player,
    rcon_ban_player,
)

from ui import close_browser, minimize_browser


def check_headers() -> dict:
    if "WebView2" in request.headers["Sec-Ch-Ua"]:
        webview_headers = {"webview": True}
    else:
        webview_headers = {"webview": False}
    return webview_headers


views = Blueprint("views", __name__)


# Define a simple route
@views.route("/")
def home():
    webview_headers = check_headers()
    return render_template("home.html", webview_headers=webview_headers)


@views.route("/loadrcon")
def loadrcon():
    webview_headers = check_headers()
    return render_template("rcon_loader.html", webview_headers=webview_headers)


@views.route("/rcon")
def rcon():
    webview_headers = check_headers()
    return render_template("rcon.html", webview_headers=webview_headers)


@views.route("/connect", methods=["POST"])
def connect():
    data = request.json
    ip_address = data["ip"]
    port = data["port"]
    password = data["password"]

    result = rcon_connect(ip_address, port, password)
    return jsonify(result)


@views.route("/broadcast", methods=["POST"])
def broadcast():
    data = request.json
    ip_address = data["ip"]
    port = data["port"]
    password = data["password"]
    message = data["message"]

    result = rcon_broadcast(ip_address, port, password, message)
    return jsonify(result)


@views.route("/getplayers", methods=["POST"])
def getplayers():
    data = request.json
    ip_address = data["ip"]
    port = data["port"]
    password = data["password"]

    result = rcon_fetch_players(ip_address, port, password)
    return jsonify(result)


@views.route("/kickplayer", methods=["POST"])
def kickplayer():
    data = request.json
    ip_address = data["ip"]
    port = data["port"]
    password = data["password"]
    player_steamid = data["player_steamid"]

    result = rcon_kick_player(ip_address, port, password, player_steamid)
    return jsonify(result)


@views.route("/banplayer", methods=["POST"])
def banplayer():
    data = request.json
    ip_address = data["ip"]
    port = data["port"]
    password = data["password"]
    player_steamid = data["player_steamid"]

    result = rcon_ban_player(ip_address, port, password, player_steamid)
    return jsonify(result)


@views.route("/close")
def close():
    close_browser()
    return "", 204


@views.route("/minimize")
def minimize():
    minimize_browser()
    return "", 204
