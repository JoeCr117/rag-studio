"""Everything the create-database form offers: engines, embedding models, runtimes, chunking and search options."""

import re
from dataclasses import asdict, dataclass

SEARCH_MODES = ("hybrid", "vector")
CHUNK_MIN_TOKENS = (100, 150, 200, 300)
CHUNK_MAX_TOKENS = (256, 400, 512, 800, 1024)
CHUNK_OVERLAP_TOKENS = (0, 20, 40, 80)
DEFAULTS = {
    "engine": "pgvector",
    "embedding_model": "qwen3-embedding-0.6b-q8",
    "embedder_runtime": "cpu",
    "chunk_min_tokens": 150,
    "chunk_max_tokens": 400,
    "chunk_overlap_tokens": 40,
    "search_mode": "hybrid",
}


@dataclass(frozen=True)
class EmbeddingModel:
    key: str
    label: str
    repo: str
    file: str
    tokenizer: str
    """Hugging Face repo whose tokenizer measures chunk sizes in this model's tokens."""
    dimensions: int
    pooling: str
    query_prefix: str
    size_gb: float
    document_prefix: str = ""
    notes: str = ""


QWEN_QUERY_PREFIX = "Instruct: Given a search query, retrieve the passages that answer it\nQuery:"

# Only models whose GGUF and tokenizer download without a Hugging Face login. Above 4,000 dimensions pgvector cannot
# index the vectors at all (halfvec's HNSW limit), which rules out Qwen3-Embedding-8B (4,096).
EMBEDDING_MODELS = {
    model.key: model
    for model in (
        EmbeddingModel(
            key="qwen3-embedding-0.6b-q8",
            label="Qwen3-Embedding 0.6B (Q8, 1024 dims)",
            repo="Qwen/Qwen3-Embedding-0.6B-GGUF",
            file="Qwen3-Embedding-0.6B-Q8_0.gguf",
            tokenizer="Qwen/Qwen3-Embedding-0.6B",
            dimensions=1024,
            pooling="last",
            query_prefix=QWEN_QUERY_PREFIX,
            size_gb=0.64,
            notes="Small and fast; follows an instruction prefix on queries.",
        ),
        EmbeddingModel(
            key="qwen3-embedding-4b-q4km",
            label="Qwen3-Embedding 4B (Q4_K_M, 2560 dims)",
            repo="Qwen/Qwen3-Embedding-4B-GGUF",
            file="Qwen3-Embedding-4B-Q4_K_M.gguf",
            tokenizer="Qwen/Qwen3-Embedding-4B",
            dimensions=2560,
            pooling="last",
            query_prefix=QWEN_QUERY_PREFIX,
            size_gb=2.5,
            notes="Larger and more accurate; slow on CPU. Stored as halfvec because it exceeds 2,000 dimensions.",
        ),
        EmbeddingModel(
            key="nomic-embed-text-v1.5-q8",
            label="nomic-embed-text v1.5 (Q8, 768 dims)",
            repo="nomic-ai/nomic-embed-text-v1.5-GGUF",
            file="nomic-embed-text-v1.5.Q8_0.gguf",
            tokenizer="nomic-ai/nomic-embed-text-v1.5",
            dimensions=768,
            pooling="mean",
            query_prefix="search_query: ",
            document_prefix="search_document: ",
            size_gb=0.15,
            notes="Tiny English model; marks queries and documents with task prefixes.",
        ),
        EmbeddingModel(
            key="bge-m3-q8",
            label="BGE-M3 (Q8, 1024 dims)",
            repo="gpustack/bge-m3-GGUF",
            file="bge-m3-Q8_0.gguf",
            tokenizer="BAAI/bge-m3",
            dimensions=1024,
            pooling="cls",
            query_prefix="",
            size_gb=0.63,
            notes="Multilingual; no prefixes.",
        ),
    )
}


def embedder_name(model_key: str, runtime: str) -> str:
    """Container name and network alias of the embedder serving `model_key` on `runtime`; databases share it."""
    return f"embed-{runtime}-{re.sub(r'[^a-z0-9]+', '-', model_key.lower()).strip('-')}"


def form_options(engines: list[str], model_status: dict[str, str], runtimes: tuple[str, ...]) -> dict:
    """`model_status`: model key -> "downloaded", "downloading" or "missing".
    `runtimes`: the ones this install offers."""
    return {
        "engines": engines,
        "embedding_models": [
            asdict(model) | {"download_status": model_status.get(model.key, "missing")}
            for model in EMBEDDING_MODELS.values()
        ],
        "runtimes": list(runtimes),
        "search_modes": list(SEARCH_MODES),
        "chunk_min_tokens": list(CHUNK_MIN_TOKENS),
        "chunk_max_tokens": list(CHUNK_MAX_TOKENS),
        "chunk_overlap_tokens": list(CHUNK_OVERLAP_TOKENS),
        "defaults": DEFAULTS,
    }


def invalid_settings(values: dict, engines: list[str], runtimes: tuple[str, ...]) -> list[str]:
    """Names the fields whose values the form does not offer; empty when every value is valid."""
    allowed = {
        "engine": engines,
        "embedding_model": list(EMBEDDING_MODELS),
        "embedder_runtime": runtimes,
        "chunk_min_tokens": CHUNK_MIN_TOKENS,
        "chunk_max_tokens": CHUNK_MAX_TOKENS,
        "chunk_overlap_tokens": CHUNK_OVERLAP_TOKENS,
        "search_mode": SEARCH_MODES,
    }
    problems = [
        f"{field}={values.get(field)!r}" for field, options in allowed.items() if values.get(field) not in options
    ]
    if not problems and values["chunk_min_tokens"] >= values["chunk_max_tokens"]:
        problems.append("chunk_min_tokens must be below chunk_max_tokens")
    return problems
