from pathlib import Path

import yaml

from studio.databases.catalog import DEFAULTS, invalid_settings
from studio.inference.servers import generator_start_warning, reranker_start_warning
from studio.runtimes import RUNTIMES, available_runtimes

PROJECT = Path(__file__).resolve().parents[2]


def _services(file_name: str) -> dict:
    return yaml.safe_load((PROJECT / file_name).read_text(encoding="utf-8"))["services"]


def test_the_gpu_is_offered_only_when_the_containers_have_one():
    assert available_runtimes(True) == RUNTIMES
    assert available_runtimes(False) == ("cpu",)


def test_a_cpu_only_install_refuses_gpu_embedders():
    gpu_database = DEFAULTS | {"embedder_runtime": "gpu"}
    assert invalid_settings(gpu_database, ["pgvector"], available_runtimes(False)) == ["embedder_runtime='gpu'"]
    assert invalid_settings(gpu_database, ["pgvector"], available_runtimes(True)) == []


def test_cpu_starts_skip_the_vram_check():
    assert generator_start_warning("gemma-4-26b-a4b-q4km", "cpu", 32768) is None
    assert reranker_start_warning("qwen3-reranker-0.6b-q8", "cpu") is None


def test_only_the_gpu_compose_file_reserves_an_nvidia_gpu():
    base, gpu = _services("compose.yaml"), _services("compose.gpu.yaml")
    assert not any("deploy" in service for service in base.values())
    assert set(gpu) == {"api", "worker"}
    for service in gpu.values():
        assert service["environment"]["GPU_AVAILABLE"] == "1"
        assert service["deploy"]["resources"]["reservations"]["devices"][0]["driver"] == "nvidia"
