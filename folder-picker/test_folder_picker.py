import http.client
import threading
from http.server import HTTPServer

import pytest

from folder_picker import FolderPickerHandler, is_rag_studio_page, start_folder, windows_path

RAG_STUDIO_PAGE = {"Origin": "http://localhost:3000", "Host": "127.0.0.1:8010", "X-RAG-Studio": "1"}


@pytest.fixture
def running_helper():
    server = HTTPServer(("127.0.0.1", 0), FolderPickerHandler)
    loop = threading.Thread(target=server.serve_forever)
    loop.start()
    yield server, loop
    server.shutdown()
    loop.join()
    server.server_close()


def post(server: HTTPServer, path: str, headers: dict) -> int:
    connection = http.client.HTTPConnection(*server.server_address, timeout=5)
    connection.request("POST", path, headers=headers)
    return connection.getresponse().status


def test_shutdown_from_rag_studio_page_stops_the_helper(running_helper):
    server, loop = running_helper
    assert post(server, "/shutdown", RAG_STUDIO_PAGE) == 200
    loop.join(timeout=5)
    assert not loop.is_alive()


def test_shutdown_without_the_marker_header_is_refused_and_the_helper_keeps_running(running_helper):
    server, loop = running_helper
    assert post(server, "/shutdown", {**RAG_STUDIO_PAGE, "X-RAG-Studio": ""}) == 403
    assert post(server, "/shutdown", {**RAG_STUDIO_PAGE, "Origin": "https://evil.example"}) == 403
    assert loop.is_alive()


@pytest.mark.parametrize("origin", ["http://localhost:3000", "http://127.0.0.1:3000"])
def test_rag_studio_page_is_allowed(origin):
    assert is_rag_studio_page(origin, "127.0.0.1:8010")


@pytest.mark.parametrize(
    ("origin", "host"),
    [
        ("https://evil.example", "127.0.0.1:8010"),
        (None, "127.0.0.1:8010"),
        ("http://localhost:3000", "evil.example:8010"),
        ("http://localhost:3001", "localhost:8010"),
    ],
)
def test_other_pages_and_rebound_hosts_are_refused(origin, host):
    assert not is_rag_studio_page(origin, host)


def test_tk_paths_become_windows_paths_and_cancel_becomes_none():
    assert windows_path("W:/Projects/My Notes") == r"W:\Projects\My Notes"
    assert windows_path("C:/") == "C:\\"
    assert windows_path("") is None


def test_the_dialog_opens_at_the_typed_folder_only_when_it_exists(tmp_path):
    assert start_folder(str(tmp_path)) == str(tmp_path)
    assert start_folder(str(tmp_path / "missing")) is None
    assert start_folder("") is None
