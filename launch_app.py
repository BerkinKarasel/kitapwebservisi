import os
import socket
import sys
import threading
import time
import webbrowser

import app


HOST = "127.0.0.1"
PORT = 8000
APP_URL = f"http://{HOST}:{PORT}"


def is_server_running():
    try:
        with socket.create_connection((HOST, PORT), timeout=0.5):
            return True
    except OSError:
        return False


def wait_for_server(timeout_seconds=15):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if is_server_running():
            return True
        time.sleep(0.4)
    return False


def open_browser():
    try:
        os.startfile(APP_URL)
        return
    except Exception:
        pass

    webbrowser.open(APP_URL)


def main():
    if is_server_running():
        open_browser()
        return

    server_thread = threading.Thread(target=app.run_server, daemon=False)
    server_thread.start()

    if not wait_for_server():
        raise SystemExit("Sunucu baslatilamadi.")

    open_browser()
    server_thread.join()


if __name__ == "__main__":
    main()
