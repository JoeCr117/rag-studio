"""The only code that touches Docker. Each action validates its input and runs a fixed `docker` argument list.

The app containers send requests here instead of holding the Docker socket themselves, so a bug in the app cannot
run arbitrary containers or mount arbitrary paths.
"""

import json
import re
import subprocess
from pathlib import PureWindowsPath

PROJECT = "rag-studio"
NETWORK = f"{PROJECT}_default"
MODELS_VOLUME = f"{PROJECT}_models"
DESKTOP_HOST_ROOT = "/run/desktop/mnt/host"
CHECK_IMAGE = "alpine:3.22"
COMPOSE_IMAGE = "docker:28-cli"
SHUTDOWN_DELAY_SECONDS = 2
LLAMA_CPP_BUILD = "b12019"
"""Pinned: RAG Studio passes flags and request fields (`--reasoning`, `-ncmoe`, `chat_template_kwargs`) that a later
build may rename. Change it only after starting an embedder, the generator and the reranker on the new build."""
LLAMA_IMAGES = {
    "cpu": f"ghcr.io/ggml-org/llama.cpp:server-{LLAMA_CPP_BUILD}",
    "gpu": f"ghcr.io/ggml-org/llama.cpp:server-cuda-{LLAMA_CPP_BUILD}",
}
EMBEDDER_CONTEXT = "2048"
RERANKER_CONTEXT = "1024"
GENERATOR_CONTEXTS = (4096, 8192, 16384, 32768)
MAX_CPU_MOE_LAYERS = 99
GENERATOR_NAME = "generator"
RERANKER_NAME = "reranker"

CONTAINER_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
MODEL_FILE = re.compile(r"^[A-Za-z0-9._-]+\.gguf$")
POOLING = {"last", "mean", "cls"}


class ActionError(ValueError):
    pass


def desktop_host_path(windows_path: str) -> str:
    """`W:\\Docs\\Notes` -> `/run/desktop/mnt/host/w/Docs/Notes`, the form Docker Desktop's VM mounts host drives at."""
    path = PureWindowsPath(windows_path)
    if not path.drive or len(path.drive) != 2 or not path.drive[0].isalpha() or not path.is_absolute():
        raise ActionError(f"Not an absolute Windows path with a drive letter: {windows_path!r}")
    if ".." in path.parts or any(character in windows_path for character in '"\n\r\t'):
        raise ActionError(f"Path contains a forbidden sequence: {windows_path!r}")
    return "/".join([DESKTOP_HOST_ROOT, path.drive[0].lower(), *path.parts[1:]])


def llama_server_arguments(name: str, role: str, runtime: str, model_file: str, role_flags: list[str]) -> list[str]:
    """`docker run` for one llama.cpp server container, reachable on the compose network at http://<name>:8080."""
    if not CONTAINER_NAME.match(name):
        raise ActionError(f"Invalid container name {name!r}")
    if runtime not in LLAMA_IMAGES:
        raise ActionError(f"Unknown runtime {runtime!r}")
    if not MODEL_FILE.match(model_file):
        raise ActionError(f"Invalid model file {model_file!r}")
    placement = ["--gpus", "all"] if runtime == "gpu" else []
    layers = ["-ngl", "99"] if runtime == "gpu" else ["-ngl", "0"]
    return [
        "docker",
        "run",
        "-d",
        "--name",
        f"{PROJECT}-{name}",
        "--network",
        NETWORK,
        "--network-alias",
        name,
        "--label",
        f"{PROJECT}.role={role}",
        "-v",
        f"{MODELS_VOLUME}:/models:ro",
        *placement,
        LLAMA_IMAGES[runtime],
        "-m",
        f"/models/{model_file}",
        *role_flags,
        "--parallel",
        "1",
        *layers,
        "--host",
        "0.0.0.0",
        "--port",
        "8080",
        "--no-webui",
    ]


def embedder_arguments(name: str, runtime: str, model_file: str, pooling: str) -> list[str]:
    if pooling not in POOLING:
        raise ActionError(f"Unknown pooling {pooling!r}")
    flags = [
        "--embedding",
        "--pooling",
        pooling,
        "-c",
        EMBEDDER_CONTEXT,
        "-b",
        EMBEDDER_CONTEXT,
        "-ub",
        EMBEDDER_CONTEXT,
    ]
    return llama_server_arguments(name, "embedder", runtime, model_file, flags)


def generator_arguments(runtime: str, model_file: str, context: int, cpu_moe_layers: int) -> list[str]:
    """q8_0 KV cache halves its memory (needs flash attention). On the GPU, `-ncmoe` keeps that many MoE layers'
    experts in system RAM so a model larger than VRAM still fits; on the CPU everything is in system RAM already."""
    if context not in GENERATOR_CONTEXTS:
        raise ActionError(f"Context must be one of {GENERATOR_CONTEXTS}")
    if not 0 <= cpu_moe_layers <= MAX_CPU_MOE_LAYERS:
        raise ActionError(f"cpu_moe_layers must be 0..{MAX_CPU_MOE_LAYERS}")
    flags = [
        "-c",
        str(context),
        "-fa",
        "on",
        "--cache-type-k",
        "q8_0",
        "--cache-type-v",
        "q8_0",
        "--reasoning",
        "off",
        *(["-ncmoe", str(cpu_moe_layers)] if cpu_moe_layers and runtime == "gpu" else []),
    ]
    return llama_server_arguments(GENERATOR_NAME, "generator", runtime, model_file, flags)


def reranker_arguments(runtime: str, model_file: str) -> list[str]:
    flags = ["--reranking", "-c", RERANKER_CONTEXT, "-b", RERANKER_CONTEXT, "-ub", RERANKER_CONTEXT]
    return llama_server_arguments(RERANKER_NAME, "reranker", runtime, model_file, flags)


def run(arguments: list[str], timeout: float = 300) -> subprocess.CompletedProcess:
    return subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)


def check_source(host_path: str) -> None:
    """Confirms the host path exists by bind-mounting it into a throwaway container."""
    mount = f"type=bind,src={desktop_host_path(host_path)},dst=/check,readonly"
    completed = run(["docker", "run", "--rm", "--mount", mount, CHECK_IMAGE, "true"], timeout=120)
    if completed.returncode:
        raise ActionError(f"{host_path} is not reachable from Docker: {completed.stderr.strip()}")


def start_embedder(name: str, runtime: str, model_file: str, pooling: str) -> str:
    """Embedders are shared by databases with the same model and runtime, so a running one is reused."""
    arguments = embedder_arguments(name, runtime, model_file, pooling)
    if container_state(name) == "running":
        return "already running"
    return _replace_container(name, arguments)


def start_generator(runtime: str, model_file: str, context: int, cpu_moe_layers: int) -> str:
    """One generator at a time: starting replaces whatever model ran before."""
    return _replace_container(GENERATOR_NAME, generator_arguments(runtime, model_file, context, cpu_moe_layers))


def start_reranker(runtime: str, model_file: str) -> str:
    return _replace_container(RERANKER_NAME, reranker_arguments(runtime, model_file))


def _replace_container(name: str, arguments: list[str]) -> str:
    run(["docker", "rm", "-f", f"{PROJECT}-{name}"])
    completed = run(arguments)
    if completed.returncode:
        raise ActionError(f"Starting {name} failed: {completed.stderr.strip()}")
    return "started"


def stop_container(name: str) -> str:
    if not CONTAINER_NAME.match(name):
        raise ActionError(f"Invalid container name {name!r}")
    run(["docker", "rm", "-f", f"{PROJECT}-{name}"])
    return "stopped"


def shutdown_arguments() -> list[str]:
    """A helper container outside the compose project runs `compose down`, because this container is one of those
    being stopped and would die mid-command. The delay lets this action answer first. Volumes are kept."""
    return [
        "docker",
        "run",
        "-d",
        "--rm",
        "--name",
        f"{PROJECT}-shutdown",
        "-v",
        "/var/run/docker.sock:/var/run/docker.sock",
        COMPOSE_IMAGE,
        "sh",
        "-c",
        f"sleep {SHUTDOWN_DELAY_SECONDS} && docker compose --project-name {PROJECT} down",
    ]


def shutdown() -> str:
    """Removes the containers the app started (embedders, generator, reranker), then stops the compose stack."""
    names = [f"{PROJECT}-{container['name']}" for container in managed_containers()]
    if names:
        run(["docker", "rm", "-f", *names])
    run(["docker", "rm", "-f", f"{PROJECT}-shutdown"])
    completed = run(shutdown_arguments())
    if completed.returncode:
        raise ActionError(f"Starting the shutdown helper failed: {completed.stderr.strip()}")
    return f"removed {len(names)} app container(s); the stack stops in {SHUTDOWN_DELAY_SECONDS}s"


def container_state(name: str) -> str | None:
    completed = run(["docker", "inspect", "--format", "{{.State.Status}}", f"{PROJECT}-{name}"])
    return completed.stdout.strip() if completed.returncode == 0 else None


def managed_containers() -> list[dict]:
    completed = run(["docker", "ps", "-a", "--filter", f"label={PROJECT}.role", "--format", "{{json .}}"])
    rows = [json.loads(line) for line in completed.stdout.splitlines() if line.strip()]
    return [
        {"name": row["Names"].removeprefix(f"{PROJECT}-"), "state": row["State"], "status": row["Status"]}
        for row in rows
    ]
