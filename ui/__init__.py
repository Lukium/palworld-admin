import webview


window = None
iconpath = "ui/icon.png"


def open_browser():
    global window
    url = "http://localhost:8210"
    window = webview.create_window(
        "Palworld Dedicated Server Tools",
        url=url,
        width=800,
        height=1000,
        resizable=False,
        fullscreen=False,
        frameless=True,
    )

    webview.start()


def close_browser():
    global window
    if window:
        window.destroy()
        window = None


def minimize_browser():
    global window
    if window:
        window.minimize()
