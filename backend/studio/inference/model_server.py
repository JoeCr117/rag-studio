"""Calls to a llama.cpp server, with failures turned into a message a person can act on."""

from types import TracebackType
from typing import Self

import httpx


class ModelServerError(RuntimeError):
    """A model server refused a request or did not answer; the message says which and why."""


def server_message(response: httpx.Response) -> str:
    """llama.cpp's own explanation (`{"error": {"message": ...}}`), else the raw body."""
    try:
        error = response.json().get("error", {})
    except ValueError:
        return response.text.strip() or response.reason_phrase
    return error.get("message", "") if isinstance(error, dict) else str(error)


def post_json(client: httpx.Client, path: str, payload: dict, server_name: str) -> dict:
    try:
        response = client.post(path, json=payload)
    except httpx.TimeoutException as error:
        raise ModelServerError(f"The {server_name} did not answer in time") from error
    except httpx.TransportError as error:
        raise ModelServerError(f"The {server_name} is not answering: start it again ({error})") from error
    if response.is_error:
        raise ModelServerError(
            f"The {server_name} refused the request ({response.status_code}): {server_message(response)}"
        )
    return response.json()


class ModelServerClient:
    """Base for one model server's client. Use as a context manager so its connections close. Tests pass an
    `httpx.MockTransport` as `transport`."""

    def __init__(
        self, base_url: str, server_name: str, timeout: float, transport: httpx.BaseTransport | None = None
    ) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout, transport=transport)
        self._server_name = server_name

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None
    ) -> None:
        self._client.close()

    def _post(self, path: str, payload: dict) -> dict:
        return post_json(self._client, path, payload, self._server_name)
