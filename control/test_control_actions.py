import pytest

from control_actions import (
    LLAMA_IMAGES,
    ActionError,
    desktop_host_path,
    embedder_arguments,
    generator_arguments,
    reranker_arguments,
    shutdown_arguments,
)


def test_windows_paths_map_to_docker_desktop_host_mounts():
    assert desktop_host_path(r"W:\Projects\My Notes") == "/run/desktop/mnt/host/w/Projects/My Notes"
    assert desktop_host_path("C:/Users/Alex") == "/run/desktop/mnt/host/c/Users/Alex"


@pytest.mark.parametrize("path", ["Projects\\Notes", "/etc", r"W:\a\..\b", 'W:\\a"b', "\\\\server\\share\\x"])
def test_relative_traversing_or_unsafe_paths_are_rejected(path):
    with pytest.raises(ActionError):
        desktop_host_path(path)


def test_gpu_embedders_get_the_cuda_image_and_all_layers():
    arguments = embedder_arguments("embed-gpu-qwen", "gpu", "Qwen3-Embedding-0.6B-Q8_0.gguf", "last")
    assert "--gpus" in arguments and LLAMA_IMAGES["gpu"] in arguments
    assert arguments[arguments.index("-ngl") + 1] == "99"
    assert "rag-studio_models:/models:ro" in arguments


@pytest.mark.parametrize(
    ("name", "runtime", "model_file", "pooling"),
    [
        ("Bad Name", "cpu", "m.gguf", "last"),
        ("ok", "tpu", "m.gguf", "last"),
        ("ok", "cpu", "../m.gguf", "last"),
        ("ok", "cpu", "m.gguf", "max"),
    ],
)
def test_embedder_inputs_are_validated(name, runtime, model_file, pooling):
    with pytest.raises(ActionError):
        embedder_arguments(name, runtime, model_file, pooling)


def test_generator_runs_on_gpu_with_quantized_kv_cache_and_optional_cpu_experts():
    arguments = generator_arguments("gpu", "Qwen3.5-9B-Q4_K_M.gguf", 8192, 0)
    assert LLAMA_IMAGES["gpu"] in arguments
    assert arguments[arguments.index("-c") + 1] == "8192"
    assert arguments[arguments.index("--cache-type-k") + 1] == "q8_0"
    assert "-ncmoe" not in arguments
    moe = generator_arguments("gpu", "big.gguf", 8192, 18)
    assert moe[moe.index("-ncmoe") + 1] == "18"


def test_generator_on_the_cpu_keeps_every_layer_in_system_ram():
    arguments = generator_arguments("cpu", "big.gguf", 8192, 18)
    assert LLAMA_IMAGES["cpu"] in arguments and "--gpus" not in arguments
    assert arguments[arguments.index("-ngl") + 1] == "0" and "-ncmoe" not in arguments


@pytest.mark.parametrize(("context", "layers"), [(1000, 0), (8192, -1), (8192, 100)])
def test_generator_inputs_are_validated(context, layers):
    with pytest.raises(ActionError):
        generator_arguments("gpu", "model.gguf", context, layers)


def test_reranker_uses_rerank_mode_on_either_runtime():
    cpu = reranker_arguments("cpu", "qwen3-reranker-0.6b-q8_0.gguf")
    assert "--reranking" in cpu and LLAMA_IMAGES["cpu"] in cpu and "--gpus" not in cpu
    assert "--gpus" in reranker_arguments("gpu", "qwen3-reranker-0.6b-q8_0.gguf")


def test_shutdown_runs_compose_down_from_a_helper_outside_the_project_and_keeps_volumes():
    arguments = shutdown_arguments()
    assert arguments[:5] == ["docker", "run", "-d", "--rm", "--name"]
    assert "/var/run/docker.sock:/var/run/docker.sock" in arguments
    command = arguments[-1]
    assert command.startswith("sleep ") and command.endswith("docker compose --project-name rag-studio down")
    assert "-v" not in command.split()
