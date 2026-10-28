import argparse
import os
from pathlib import Path
import signal
import socket
import subprocess
import time

import webview

from .api import InputGateApi
from .manager import DeviceManager


_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def _terminateProcess(process):
    # Vite can spawn children; stop its whole process group.
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)


def _isPortOpen(port):
    try:
        with socket.create_connection(('localhost', port), timeout=0.5):
            return True
    except OSError:
        return False


def _openWindow(url):
    """Open the desktop window with its backend API."""
    manager = DeviceManager()
    api = InputGateApi(manager)
    webview.create_window(
        title="InputGate",
        url=url,
        js_api=api,
        width=1000,
        height=700,
        min_size=(600, 500),
    )
    webview.start()


def start():
    """Start using the built frontend."""
    index_path = _FRONTEND_DIR / "dist" / "index.html"
    if not index_path.is_file():
        raise RuntimeError("Frontend build missing. Run npm run build in src/frontend first.")
    _openWindow(str(index_path))


def startDev(port=5173):
    """Start with the Vite development server."""
    while _isPortOpen(port):
        port += 1
    print(f"Starting dev server on port {port}...")
    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(port), "--strictPort"],
        cwd=_FRONTEND_DIR,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # Wait for Vite before opening the window; always release it on failure or close.
        deadline = time.monotonic() + 5
        while not _isPortOpen(port):
            if process.poll() is not None:
                raise RuntimeError("The frontend development server exited before startup.")
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Port {port} did not open within 5 seconds.")
            time.sleep(0.1)
        _openWindow(f"http://localhost:{port}")
    finally:
        _terminateProcess(process)


def main():
    parser = argparse.ArgumentParser(description="Manage Linux input devices.")
    parser.add_argument("--dev", action="store_true", help="Use the Vite development server")
    args = parser.parse_args()
    if args.dev:
        startDev()
    else:
        start()


if __name__ == "__main__":
    main()
