import webview


class BrowserManager:
    """Class to manage the webview browser window. This class is used to open, close, and minimize the browser window."""

    def __init__(self, iconpath="ui/icon.png"):
        self.window = None
        self.iconpath = iconpath

    def open_browser(self):
        """Open the webview browser window."""
        url = "http://localhost:8210"
        self.window = webview.create_window(
            "Palworld Dedicated Server Tools",
            url=url,
            width=800,
            height=1000,
            resizable=False,
            fullscreen=False,
            frameless=True,
        )
        webview.start()

    def close_browser(self):
        """Close the webview browser window."""
        if self.window:
            self.window.destroy()
            self.window = None

    def minimize_browser(self):
        """Minimize the webview browser window."""
        if self.window:
            self.window.minimize()
