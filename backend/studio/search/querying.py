"""Runs one search against a database: embed the query with the database's own model, ask its engine, and optionally
let the reranker re-order a larger candidate pool."""

import time
from dataclasses import asdict, dataclass, replace

from studio.databases.embedders import embedder_for
from studio.databases.engines import engine_named
from studio.databases.engines.base import SearchHit
from studio.inference.clients import RerankerClient
from studio.models import VectorDatabase


@dataclass(frozen=True)
class SearchResult:
    hits: list[SearchHit]
    mode: str
    embed_ms: float
    search_ms: float
    rerank_ms: float | None = None
    rerank_pool: int | None = None


def rerank_document(hit: SearchHit) -> str:
    return f"{hit.path}\n{hit.content}"


def reranked(hits: list[SearchHit], scores: list[float], limit: int) -> list[SearchHit]:
    scored = [replace(hit, rerank_score=score) for hit, score in zip(hits, scores, strict=True)]
    return sorted(scored, key=lambda hit: hit.rerank_score, reverse=True)[:limit]


def search_database(
    database: VectorDatabase, query: str, limit: int, mode: str, rerank_pool: int | None = None
) -> SearchResult:
    """`rerank_pool`: fetch that many candidates and keep the reranker's best `limit`; None skips reranking."""
    started = time.perf_counter()
    with embedder_for(database) as embedder:
        vector = embedder.embed_query(query)
    embedded = time.perf_counter()
    hits = engine_named(database.engine).search(database.id, vector, query, max(limit, rerank_pool or 0), mode)
    searched = time.perf_counter()
    if rerank_pool is None:
        return SearchResult(
            hits=hits, mode=mode, embed_ms=(embedded - started) * 1000, search_ms=(searched - embedded) * 1000
        )
    with RerankerClient() as reranker:
        scores = reranker.scores(query, [rerank_document(hit) for hit in hits])
    finished = time.perf_counter()
    return SearchResult(
        hits=reranked(hits, scores, limit),
        mode=mode,
        embed_ms=(embedded - started) * 1000,
        search_ms=(searched - embedded) * 1000,
        rerank_ms=(finished - searched) * 1000,
        rerank_pool=rerank_pool,
    )


def result_view(result: SearchResult, source_names: dict[int, str]) -> dict:
    return {
        "mode": result.mode,
        "embed_ms": round(result.embed_ms, 1),
        "search_ms": round(result.search_ms, 1),
        "rerank_ms": None if result.rerank_ms is None else round(result.rerank_ms, 1),
        "rerank_pool": result.rerank_pool,
        "hits": [
            asdict(hit) | {"source_name": source_names.get(hit.source_id, f"source {hit.source_id} (unregistered)")}
            for hit in result.hits
        ],
    }
