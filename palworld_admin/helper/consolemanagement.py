""" This module contains the function to hide the console window. """

import ctypes as ct
from ctypes import wintypes as w

SW_HIDE = 0
SW_SHOW = 5


# Function to hide the console window
def hide_console():
    """Hide the console window."""
    user32 = ct.WinDLL("user32")
    # BOOL ShowWindow(HWND hWnd, int nCmdShow);
    user32.ShowWindow.argtypes = w.HWND, ct.c_int
    user32.ShowWindow.restype = w.BOOL
    # HWND FindWindowW(LPCWSTR lpClassName, LPCWSTR lpWindowName);
    user32.FindWindowW.argtypes = w.LPCWSTR, w.LPCWSTR
    user32.FindWindowW.restype = w.HWND

    # Get a handle to the console window
    whnd = ct.windll.Kernel32.GetConsoleWindow()
    # If a console window was found, make it invisible
    if whnd != 0:
        user32.ShowWindow(whnd, 0)  # 0 = SW_HIDE
