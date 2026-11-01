# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Opens Windows' own folder dialog for the Browse… button next to "Path on this machine".

It runs on Windows, outside Docker: a web page is never told a folder's full path, and the Linux containers cannot open
Windows windows. start.ps1 starts it hidden. It listens on 127.0.0.1 only and answers only RAG Studio's page. The UI's
Shut down button stops it; if the stack stops some other way, it exits once RAG Studio's API has been unreachable for a
minute.
"""

import ctypes
import json
import ntpath
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from tkinter import Tk, filedialog

PORT = 8010
ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}
ALLOWED_HOSTS = {f"127.0.0.1:{PORT}", f"localhost:{PORT}"}
"""Checking Host stops DNS rebinding, where another site's name is pointed at 127.0.0.1."""
MARKER_HEADER = "X-RAG-Studio"
"""A custom header makes a browser ask permission (a CORS preflight) before the request, so other sites cannot even
open the dialog."""
API_HEALTH_URL = "http://localhost:8000/api/health"
WATCH_INTERVAL_SECONDS = 5
EXIT_AFTER_API_GONE_SECONDS = 60
DIALOG_TITLE = "Choose a folder for RAG Studio"


def is_rag_studio_page(origin: str | None, host: str | None) -> bool:
    return origin in ALLOWED_ORIGINS and host in ALLOWED_HOSTS


def windows_path(chosen: str) -> str | None:
    """Tk answers `W:/Notes/Project`, or an empty string when the dialog is cancelled."""
    return ntpath.normpath(chosen) if chosen else None


def start_folder(typed: str) -> str | None:
    """Where the dialog opens: the path already typed, when it exists."""
    return typed if typed and os.path.isdir(typed) else None


def ask_for_folder(start: str | None) -> str | None:
    """Blocks until the dialog closes. A hidden, always-on-top owner window keeps the dialog in front of the browser."""
    owner = Tk()
    owner.withdraw()
    owner.attributes("-topmost", True)
    try:
        return windows_path(filedialog.askdirectory(parent=owner, initialdir=start, mustexist=True, title=DIALOG_TITLE))
    finally:
        owner.destroy()


class FolderPickerHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict | None = None) -> None:
        body = json.dumps(payload).encode() if payload is not None else b""
        self.send_response(status)
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST")
            self.send_header("Access-Control-Allow-Headers", f"Content-Type, {MARKER_HEADER}")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self._send(204 if is_rag_studio_page(self.headers.get("Origin"), self.headers.get("Host")) else 403)

    def do_GET(self) -> None:
        if self.path != "/health" or self.headers.get("Host") not in ALLOWED_HOSTS:
            return self._send(404, {"error": "not found"})
        self._send(200, {"ok": True})

    def do_POST(self) -> None:
        routes = {"/pick-folder": self._pick_folder, "/shutdown": self._stop}
        if self.path not in routes:
            return self._send(404, {"error": "not found"})
        if (
            not is_rag_studio_page(self.headers.get("Origin"), self.headers.get("Host"))
            or self.headers.get(MARKER_HEADER) != "1"
        ):
            return self._send(403, {"error": "only RAG Studio's page may use the folder dialog helper"})
        routes[self.path]()

    def _pick_folder(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        typed = str(json.loads(self.rfile.read(length) or b"{}").get("start", ""))
        self._send(200, {"path": ask_for_folder(start_folder(typed))})

    def _stop(self) -> None:
        """Shut down asks for this. `shutdown()` waits for the request loop, so it must run off the loop's thread."""
        self._send(200, {"ok": True})
        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format: str, *args) -> None:
        """Runs hidden, with no console to write to."""


def api_reachable() -> bool:
    try:
        with urllib.request.urlopen(API_HEALTH_URL, timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def stop_when_studio_is_gone(server: HTTPServer) -> None:
    last_seen = time.monotonic()
    while True:
        time.sleep(WATCH_INTERVAL_SECONDS)
        if api_reachable():
            last_seen = time.monotonic()
        elif time.monotonic() - last_seen > EXIT_AFTER_API_GONE_SECONDS:
            server.shutdown()
            return


def main() -> None:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # sharp dialog text on scaled displays
    server = HTTPServer(("127.0.0.1", PORT), FolderPickerHandler)
    threading.Thread(target=stop_when_studio_is_gone, args=(server,), daemon=True).start()
    with server:
        server.serve_forever()


if __name__ == "__main__":
    main()
