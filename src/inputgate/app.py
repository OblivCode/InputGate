import webview, atexit, subprocess, time, socket, os, signal
from pathlib import Path
from .api import InputGateApi
from .manager import DeviceManager

def terminateProcess(process):
    os.killpg(process.pid, signal.SIGTERM)

def isPortOpen(port):
    try:
        with socket.create_connection(('localhost', port), timeout=0.5):
            return True
    except (ConnectionRefusedError, TimeoutError, OSError):
        return False

def startDev(port=5173):
    while isPortOpen(port):
        port += 1
    # spawn npm dev server
    print(f"Starting dev server on port {port}...")
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    process = subprocess.Popen(f"npm run dev -- --port {port} --strictPort".split(), cwd=frontend_dir, start_new_session=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # wait until port accepts connections
    start_time = time.time()
    max_sec = 5
    port_open = False
    while time.time() - start_time < max_sec:
        if isPortOpen(port):
            port_open = True
            break
        time.sleep(0.1)

    if not port_open:
        terminateProcess(process)
        raise RuntimeError(f"Port {port} did not open within {max_sec} seconds.")
    
    # open webview
    manager = DeviceManager()
    api = InputGateApi(manager)
    window = webview.create_window(
        title="InputGate",
        url="http://localhost:"+str(port),
        js_api=api,
        width=1000,
        height=700,
        min_size=(600, 500),
    )
    try:
        webview.start()
    finally:
        terminateProcess(process)


def main():
    startDev()

if __name__ == "__main__":
    main()