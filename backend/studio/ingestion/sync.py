"""Makes one source's documents in one database match the source's files: add new, re-embed changed, remove missing."""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from studio.databases.engines.base import StoredChunk, VectorEngine
from studio.ingestion.chunking import file_header, is_markdown, splitter_for
from studio.ingestion.embedding_client import EmbeddingClient
from studio.jobs.progress import Progress, ProgressReport, ignore_progress
from studio.sources.scanning import ScanResult

Splitter = Callable[[str], list[str]]
"""text -> chunks, for one file type."""


@dataclass(frozen=True)
class SyncSummary:
    added: int
    updated: int
    unchanged: int
    removed: int
    chunks: int


def removed_paths(stored: dict[str, str], present: set[str]) -> list[str]:
    return sorted(stored.keys() - present)


def content_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sync_source(
    database_id: int,
    source_id: int,
    source_name: str,
    root: Path,
    scan: ScanResult,
    engine: VectorEngine,
    embedder: EmbeddingClient,
    splitter_for_path: Callable[[str], Splitter],
    on_progress: ProgressReport = ignore_progress,
) -> SyncSummary:
    """Reports progress before each file, naming it, so a slow file shows as the one being worked on."""
    stored = engine.document_hashes(database_id, source_id)
    added = updated = unchanged = chunks_written = 0
    for done, file in enumerate(scan.files):
        on_progress(Progress(done=done, total=len(scan.files), unit="files", detail=file.path))
        data = (root / file.path).read_bytes()
        digest = content_hash(data)
        if stored.get(file.path) == digest:
            unchanged += 1
            continue
        text = data.decode("utf-8", errors="replace")
        pieces = splitter_for_path(file.path)(text)
        header = file_header(source_name, file.path)
        embedding_texts = [f"{header}\n\n{piece}" for piece in pieces]
        vectors = embedder.embed_documents(embedding_texts) if pieces else []
        chunks = [
            StoredChunk(index=index, content=piece, embedding_text=embedding_text, vector=vector)
            for index, (piece, embedding_text, vector) in enumerate(zip(pieces, embedding_texts, vectors, strict=True))
        ]
        engine.replace_document(database_id, source_id, file.path, digest, chunks)
        chunks_written += len(chunks)
        if file.path in stored:
            updated += 1
            logger.info("  ~ {}  ({} chunks)", file.path, len(chunks))
        else:
            added += 1
            logger.info("  + {}  ({} chunks)", file.path, len(chunks))
    missing = removed_paths(stored, {file.path for file in scan.files})
    if missing:
        engine.remove_documents(database_id, source_id, missing)
        for path in missing:
            logger.info("  - {}", path)
    return SyncSummary(added=added, updated=updated, unchanged=unchanged, removed=len(missing), chunks=chunks_written)


def splitters_for(tokenizer: str, min_tokens: int, max_tokens: int, overlap: int) -> Callable[[str], Splitter]:
    def for_path(path: str) -> Splitter:
        return splitter_for(tokenizer, min_tokens, max_tokens, overlap, is_markdown(path)).chunks

    return for_path
