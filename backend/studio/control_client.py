"""Requests to the control sidecar, the only service allowed to drive Docker."""

import httpx
from django.conf import settings


class ControlError(RuntimeError):
    pass


def _call(method: str, path: str, body: dict | None = None, timeout: float = 600) -> dict:
    try:
        response = httpx.request(method, f"{settings.CONTROL_URL}{path}", json=body, timeout=timeout)
    except httpx.HTTPError as error:
        raise ControlError(f"Control sidecar unreachable: {error}") from error
    payload = response.json()
    if response.status_code != 200:
        raise ControlError(payload.get("error", response.text))
    return payload


def check_source(host_path: str) -> None:
    _call("POST", "/sources/check", {"host_path": host_path}, timeout=180)


def start_embedder(name: str, runtime: str, model_file: str, pooling: str) -> str:
    return _call(
        "POST", "/embedders/start", {"name": name, "runtime": runtime, "model_file": model_file, "pooling": pooling}
    )["result"]


def start_generator(runtime: str, model_file: str, context: int, cpu_moe_layers: int) -> str:
    body = {"runtime": runtime, "model_file": model_file, "context": context, "cpu_moe_layers": cpu_moe_layers}
    return _call("POST", "/generator/start", body)["result"]


def start_reranker(runtime: str, model_file: str) -> str:
    return _call("POST", "/reranker/start", {"runtime": runtime, "model_file": model_file})["result"]


def shutdown() -> str:
    return _call("POST", "/shutdown", timeout=120)["result"]


def stop_container(name: str) -> None:
    _call("POST", "/containers/stop", {"name": name})


def containers() -> list[dict]:
    return _call("GET", "/containers", timeout=10)["containers"]
