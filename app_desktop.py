import os
import sys
import threading
import time
import socket
import subprocess

# Pornire aplicatie SMART-RECRUT ca aplicatie desktop locala.
# Nu foloseste pywebview/pythonnet, deci evita eroarea Python.Runtime.Loader.Initialize.
# Backend-ul Flask ruleaza doar pe laptop, pe 127.0.0.1, si nu este host public.

from app import app

HOST = "127.0.0.1"
PORT = 5000


def wait_port(host=HOST, port=PORT, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def start_flask():
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)


def open_desktop_window(url):
    # Deschide in fereastra de aplicatie, nu tab normal de browser.
    edge_paths = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    ]

    for exe in edge_paths + chrome_paths:
        if exe and os.path.exists(exe):
            subprocess.Popen([exe, f"--app={url}", "--new-window"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

    # Fallback: deschide browser-ul default doar daca nu exista Edge/Chrome.
    import webbrowser
    webbrowser.open(url)


if __name__ == "__main__":
    t = threading.Thread(target=start_flask, daemon=True)
    t.start()
    url = f"http://{HOST}:{PORT}"
    if wait_port():
        open_desktop_window(url)
    else:
        print("Aplicatia nu a pornit. Verifica dependentele Python.")
    # Pastreaza procesul pornit cat timp aplicatia este folosita.
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        sys.exit(0)
