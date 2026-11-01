"""HTTP front for control_actions: JSON in, JSON out, reachable only on the compose network."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import control_actions as actions


def handle(method: str, path: str, body: dict) -> dict:
    match method, path:
        case "GET", "/health":
            return {"ok": True}
        case "GET", "/containers":
            return {"containers": actions.managed_containers()}
        case "POST", "/sources/check":
            actions.check_source(body["host_path"])
            return {"ok": True}
        case "POST", "/embedders/start":
            return {
                "ok": True,
                "result": actions.start_embedder(body["name"], body["runtime"], body["model_file"], body["pooling"]),
            }
        case "POST", "/generator/start":
            result = actions.start_generator(
                body["runtime"], body["model_file"], int(body["context"]), int(body["cpu_moe_layers"])
            )
            return {"ok": True, "result": result}
        case "POST", "/reranker/start":
            return {"ok": True, "result": actions.start_reranker(body["runtime"], body["model_file"])}
        case "POST", "/shutdown":
            return {"ok": True, "result": actions.shutdown()}
        case "POST", "/containers/stop":
            return {"ok": True, "result": actions.stop_container(body["name"])}
    raise LookupError(f"{method} {path}")


class ControlHandler(BaseHTTPRequestHandler):
    def _respond(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _dispatch(self, method: str) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(length)) if length else {}
        try:
            self._respond(200, handle(method, self.path, body))
        except actions.ActionError as error:
            self._respond(400, {"ok": False, "error": str(error)})
        except (LookupError, KeyError) as error:
            self._respond(404, {"ok": False, "error": f"unknown action or field: {error}"})

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 9000), ControlHandler).serve_forever()
