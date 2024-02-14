"""Helper functions for working with threads."""

import threading


def run_function_on_thread(function, *args) -> threading.Thread:
    """Run the specified function on a new thread."""
    new_thread = threading.Thread(target=function, args=args)
    new_thread.daemon = True
    new_thread.start()
    return new_thread
