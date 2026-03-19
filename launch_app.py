import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import app


HOST = "127.0.0.1"
PORT = 8000
APP_URL = f"http://{HOST}:{PORT}"
BASE_DIR = Path(__file__).resolve().parent if not getattr(sys, "frozen", False) else Path(sys.executable).resolve().parent
CREATE_NEW_PROCESS_GROUP = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
DETACHED_PROCESS = getattr(subprocess, "DETACHED_PROCESS", 0)


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


def start_server():
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--serve"]
    else:
        command = [sys.executable, "launch_app.py", "--serve"]

    subprocess.Popen(
        command,
        cwd=BASE_DIR,
        creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
    )


def run_server_mode():
    app.run_server()


def main():
    if "--serve" in sys.argv:
        run_server_mode()
        return

    if not is_server_running():
        start_server()
        if not wait_for_server():
            raise SystemExit("Sunucu baslatilamadi.")

    webbrowser.open(APP_URL)


if __name__ == "__main__":
    main()
