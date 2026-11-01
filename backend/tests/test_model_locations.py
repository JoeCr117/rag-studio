from pathlib import Path

import yaml
from django.test import override_settings

from studio.model_locations import BUILT_IN_MODELS, model_file_location, tokenizer_location

COMPOSE_FILE = Path(__file__).resolve().parents[2] / "compose.yaml"
HOST_DIR = r"\\wsl.localhost\docker-desktop\volumes\models"


@override_settings(MODELS_DIR=Path("/models"), MODELS_HOST_DIR=HOST_DIR)
def test_model_files_are_located_in_the_volume_from_both_sides():
    location = model_file_location("Qwen/Qwen3-Embedding-0.6B-GGUF", "Qwen3-Embedding-0.6B-Q8_0.gguf")
    assert location.container_path == "/models/Qwen3-Embedding-0.6B-Q8_0.gguf"
    assert location.windows_path == HOST_DIR + r"\Qwen3-Embedding-0.6B-Q8_0.gguf"
    assert (
        location.source_url
        == "https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/blob/main/Qwen3-Embedding-0.6B-Q8_0.gguf"
    )


@override_settings(MODELS_DIR=Path("/models"), MODELS_HOST_DIR=HOST_DIR)
def test_tokenizers_are_located_in_the_hugging_face_cache_folder():
    location = tokenizer_location("Qwen/Qwen3-Embedding-0.6B")
    assert location.container_path == "/models/hf/hub/models--Qwen--Qwen3-Embedding-0.6B"
    assert location.windows_path == HOST_DIR + r"\hf\hub\models--Qwen--Qwen3-Embedding-0.6B"


def test_built_in_models_name_the_images_compose_actually_runs():
    services = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))["services"]
    for model in BUILT_IN_MODELS:
        assert services[model.service]["image"] == model.image


def test_compose_tells_the_backend_where_windows_sees_the_models_volume():
    services = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))["services"]
    host_dir = services["api"]["environment"]["MODELS_HOST_DIR"]
    assert host_dir.startswith("\\\\wsl.localhost\\") and host_dir.endswith(r"\rag-studio_models\_data")
