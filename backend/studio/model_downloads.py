"""GGUF files in the shared `models` volume, for every catalog: embedders, generators and rerankers."""

import shutil
from collections.abc import Callable
from pathlib import Path, PurePosixPath
from typing import Protocol

from django.conf import settings
from huggingface_hub import hf_hub_download
from huggingface_hub.file_download import repo_folder_name
from loguru import logger

from studio.databases.catalog import EMBEDDING_MODELS
from studio.inference.catalog import GENERATOR_MODELS, RERANKER_MODELS
from studio.jobs.progress import Progress, ProgressReport, byte_counting_tqdm, ignore_progress


class ModelFile(Protocol):
    key: str
    label: str
    repo: str
    file: str
    size_gb: float


DOWNLOADABLE_MODELS: dict[str, ModelFile] = EMBEDDING_MODELS | GENERATOR_MODELS | RERANKER_MODELS
DOWNLOAD_RECORDS = PurePosixPath(".cache/huggingface/download")
"""Where `hf_hub_download(local_dir=...)` keeps each file's metadata, lock and partial download."""
TOKENIZER_CACHE = PurePosixPath("hf/hub")
"""Hugging Face's cache inside the models volume; compose.yaml sets HF_HOME=/models/hf."""


def tokenizer_folder(repo: str) -> PurePosixPath:
    """Relative to the models volume: where the chunker's tokenizer for `repo` is cached."""
    return TOKENIZER_CACHE / repo_folder_name(repo_id=repo, repo_type="model")


def model_path(model: ModelFile) -> Path:
    return settings.MODELS_DIR / model.file


def is_downloaded(model: ModelFile) -> bool:
    return model_path(model).exists()


def download_statuses(downloading_keys: set[str]) -> dict[str, str]:
    return {
        key: "downloaded" if is_downloaded(model) else "downloading" if key in downloading_keys else "missing"
        for key, model in DOWNLOADABLE_MODELS.items()
    }


def download_progress(model: ModelFile, on_progress: ProgressReport) -> Callable[[int, int | None], None]:
    """Turns byte counts into Progress; the catalog size stands in until the server reports the file's size."""

    def on_bytes(written: int, total: int | None) -> None:
        estimate = int(model.size_gb * 1e9)
        on_progress(Progress(done=written, total=total or estimate, unit="bytes", detail=f"Downloading {model.label}"))

    return on_bytes


def ensure_downloaded(model: ModelFile, on_progress: ProgressReport = ignore_progress) -> Path:
    """Downloads the model's GGUF into the shared models volume on first use."""
    target = model_path(model)
    if not target.exists():
        logger.info("Downloading {} ({} GB) from {}", model.file, model.size_gb, model.repo)
        progress_bar = byte_counting_tqdm(download_progress(model, on_progress))
        hf_hub_download(model.repo, model.file, local_dir=settings.MODELS_DIR, tqdm_class=progress_bar)
        logger.info("Downloaded {} ({:.0f} MB)", model.file, target.stat().st_size / 1e6)
    return target


def remove_partial_downloads(models_dir: Path) -> int:
    """Deletes every `*.incomplete` file under the models volume and returns the bytes freed.

    huggingface_hub gives each download attempt its own temporary file and never resumes another attempt's, so a
    download killed by a restart, Shut down or crash leaves one behind forever. Only the worker downloads, one job at a
    time, so at worker start every partial file is an orphan: a model's GGUF, or a tokenizer in the Hugging Face cache.
    """
    partial = [path for path in models_dir.rglob("*.incomplete") if path.is_file()]
    freed = sum(path.stat().st_size for path in partial)
    for path in partial:
        path.unlink(missing_ok=True)
    return freed


def _files_linked_from(folder: Path) -> set[Path]:
    return {link.resolve() for link in folder.rglob("*") if link.is_symlink()}


def unshared_tokenizer_blobs(folder: Path) -> set[Path]:
    """The tokenizers library stores each file once in `hub/blobs/` and links to it from every repo folder that uses
    it; these are the stored files no other repo folder links to."""
    if not folder.is_dir():
        return set()
    others = [_files_linked_from(other) for other in folder.parent.glob("models--*") if other != folder]
    return _files_linked_from(folder).difference(*others)


def delete_download(model: ModelFile) -> int:
    """Removes the model's GGUF, its download records and, for an embedding model, its cached tokenizer. Returns the
    bytes freed. The next start downloads everything again."""
    files = {model_path(model), *(settings.MODELS_DIR / DOWNLOAD_RECORDS).glob(f"{model.file}.*")}
    tokenizer = getattr(model, "tokenizer", None)
    folders = []
    if tokenizer:
        cache = settings.MODELS_DIR / tokenizer_folder(tokenizer)
        files |= unshared_tokenizer_blobs(cache)
        folders = [cache, cache.parent / ".locks" / cache.name]
    freed = sum(path.stat().st_size for path in files if path.is_file())
    freed += sum(
        file.stat().st_size
        for folder in folders
        if folder.is_dir()
        for file in folder.rglob("*")
        if file.is_file() and not file.is_symlink()
    )
    for path in files:
        path.unlink(missing_ok=True)
    for folder in folders:
        shutil.rmtree(folder, ignore_errors=True)
    logger.info("Deleted {} ({:.0f} MB freed)", model.file, freed / 1e6)
    return freed
