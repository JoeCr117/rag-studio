"""Where every model RAG Studio uses is stored: downloaded files in the `models` volume, or built into an image.

Paths are given as the containers see them (`/models/...`) and as Windows Explorer opens them (MODELS_HOST_DIR, the
volume's folder inside Docker Desktop's WSL distro).
"""

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath, PureWindowsPath

from django.conf import settings

from studio.databases.catalog import EMBEDDING_MODELS
from studio.model_downloads import DOWNLOADABLE_MODELS, tokenizer_folder

HUGGING_FACE = "https://huggingface.co"


@dataclass(frozen=True)
class VolumeFile:
    """A file or folder in the models volume."""

    container_path: str
    windows_path: str
    source_url: str
    present: bool


@dataclass(frozen=True)
class BuiltInModel:
    """Ships inside a service's image; nothing is downloaded and nothing is stored in the models volume."""

    key: str
    label: str
    note: str
    """Name of the RAGStudioVault note that explains it."""
    used_for: str
    service: str
    image: str
    image_paths: tuple[str, ...]
    notes: str


BUILT_IN_MODELS = (
    BuiltInModel(
        key="qdrant-bm25",
        label="Qdrant BM25 (qdrant/bm25)",
        note="BM25",
        used_for="Keyword half of hybrid search in Qdrant databases",
        service="qdrant",
        image="qdrant/qdrant:v1.20.0",
        image_paths=("/qdrant/qdrant (compiled into the server program; there is no separate file)",),
        notes="Qdrant tokenizes and scores text itself, so no weights are downloaded.",
    ),
    BuiltInModel(
        key="postgres-english",
        label="Postgres full-text search, 'english' configuration",
        note="Full-text search",
        used_for="Keyword half of hybrid search in pgvector databases",
        service="pgvector",
        image="pgvector/pgvector:0.8.7-pg18",
        image_paths=(
            "/usr/lib/postgresql/18/lib/dict_snowball.so (Snowball English stemmer)",
            "/usr/share/postgresql/18/tsearch_data/english.stop (stop-word list)",
        ),
        notes="Rule-based stemming and stop words, not learned weights.",
    ),
)


def _in_volume(relative: PurePosixPath, source_url: str) -> VolumeFile:
    return VolumeFile(
        container_path=str(PurePosixPath(settings.MODELS_DIR) / relative),
        windows_path=str(PureWindowsPath(settings.MODELS_HOST_DIR, *relative.parts)),
        source_url=source_url,
        present=(settings.MODELS_DIR / relative).exists(),
    )


def model_file_location(repo: str, file: str) -> VolumeFile:
    return _in_volume(PurePosixPath(file), f"{HUGGING_FACE}/{repo}/blob/main/{file}")


def tokenizer_location(repo: str) -> VolumeFile:
    """Fetched on the first sync of a database that uses the embedding model."""
    return _in_volume(tokenizer_folder(repo), f"{HUGGING_FACE}/{repo}")


def model_locations() -> dict:
    """`files`: model key -> where its GGUF lives; `tokenizers`: embedding model key -> where its tokenizer lives."""
    return {
        "volume": {"container_path": str(PurePosixPath(settings.MODELS_DIR)), "windows_path": settings.MODELS_HOST_DIR},
        "files": {
            key: asdict(model_file_location(model.repo, model.file)) for key, model in DOWNLOADABLE_MODELS.items()
        },
        "tokenizers": {key: asdict(tokenizer_location(model.tokenizer)) for key, model in EMBEDDING_MODELS.items()},
        "built_in": [asdict(model) for model in BUILT_IN_MODELS],
    }
