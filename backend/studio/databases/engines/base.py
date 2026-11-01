import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredChunk:
    index: int
    content: str
    """What a reader or the model is shown."""
    embedding_text: str
    """What was embedded and is keyword-searched: the content with its file header."""
    vector: Sequence[float]


@dataclass(frozen=True)
class SearchHit:
    document_id: int
    source_id: int
    path: str
    chunk_index: int
    content: str
    score: float
    """Ranking score: the fused RRF score in hybrid mode, cosine similarity in vector mode."""
    similarity: float
    """Cosine similarity between the query and chunk vectors, 1 = same direction."""
    semantic_rank: int | None
    keyword_rank: int | None
    rerank_score: float | None = None
    """Cross-encoder relevance, set only when the search was reranked; it then decides the order."""


@dataclass(frozen=True)
class DocumentInfo:
    id: int
    source_id: int
    path: str
    chunks: int
    ingested_at: str


@dataclass(frozen=True)
class ChunkInfo:
    index: int
    content: str
    embedding_text: str
    dimensions: int
    vector_preview: list[float]
    """The first few numbers of the stored vector."""
    norm: float


PREVIEW_NUMBERS = 8


def vector_preview(vector: Sequence[float]) -> tuple[list[float], float]:
    """The first few numbers of a vector and its length (norm); normalized embeddings have norm 1."""
    values = [float(value) for value in vector]
    return [round(value, 4) for value in values[:PREVIEW_NUMBERS]], round(math.sqrt(sum(v * v for v in values)), 4)


class VectorEngine(Protocol):
    """One vector store holding many databases, each identified by the app's database id (Strategy pattern)."""

    def create(self, database_id: int, dimensions: int) -> None: ...

    def drop(self, database_id: int) -> None: ...

    def document_hashes(self, database_id: int, source_id: int) -> dict[str, str]:
        """Stored path -> content hash for one source's documents."""
        ...

    def replace_document(
        self, database_id: int, source_id: int, path: str, content_hash: str, chunks: Sequence[StoredChunk]
    ) -> None: ...

    def remove_documents(self, database_id: int, source_id: int, paths: Iterable[str]) -> None: ...

    def remove_source(self, database_id: int, source_id: int) -> int:
        """Deletes every document of one source; returns how many."""
        ...

    def counts(self, database_id: int) -> tuple[int, int]:
        """(documents, chunks)"""
        ...

    def search(self, database_id: int, vector: Sequence[float], text: str, limit: int, mode: str) -> list[SearchHit]:
        """`mode`: "hybrid" (vector and keyword rankings fused) or "vector"."""
        ...

    def documents(
        self, database_id: int, source_id: int | None, path_contains: str, limit: int
    ) -> list[DocumentInfo]: ...

    def chunks(self, database_id: int, document_id: int) -> list[ChunkInfo]: ...
