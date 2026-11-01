"""Qdrant: a dedicated vector database. Each app database is one collection, `vdb_<id>`.

Each chunk is a point with two vectors: "dense" (the embedder's vector, cosine distance) and "bm25" (a sparse keyword
vector that Qdrant computes itself from the text). Hybrid search runs both and fuses them with Qdrant's built-in
Reciprocal Rank Fusion, using the same k=60 as the pgvector engine so scores compare. Every document also gets one
vectorless point (chunk_index -1) holding its content hash, so the sync knows it was ingested even when it has no
chunks; searches never see it because it has no vectors.
"""

import hashlib
import uuid
from collections.abc import Iterable, Iterator, Sequence
from datetime import UTC, datetime

import numpy as np
from qdrant_client import QdrantClient, models

from studio.databases.engines.base import ChunkInfo, DocumentInfo, SearchHit, StoredChunk, vector_preview

CANDIDATE_POOL = 40
RRF_K = 60
DOCUMENT_POINT = -1
BM25_MODEL = "qdrant/bm25"
SCROLL_PAGE = 256
POINT_NAMESPACE = uuid.UUID("5d0f8e2a-3f4b-4c55-9a51-6f0c2b7e1d93")
INDEXED_FIELDS = {
    "source_id": models.PayloadSchemaType.INTEGER,
    "document_id": models.PayloadSchemaType.INTEGER,
    "chunk_index": models.PayloadSchemaType.INTEGER,
    "path": models.PayloadSchemaType.KEYWORD,
}


def collection_name(database_id: int) -> str:
    return f"vdb_{database_id}"


def document_id(source_id: int, path: str) -> int:
    """Stable integer id from the source and path; 60 bits keeps it a safe JSON number."""
    return int(hashlib.sha256(f"{source_id}\0{path}".encode()).hexdigest()[:15], 16)


def point_id(source_id: int, path: str, chunk_index: int) -> str:
    return str(uuid.uuid5(POINT_NAMESPACE, f"{source_id}\0{path}\0{chunk_index}"))


def matching(**fields) -> models.Filter:
    """A filter requiring every field to equal its value; a list value matches any of its items."""
    return models.Filter(
        must=[
            models.FieldCondition(
                key=key, match=models.MatchAny(any=value) if isinstance(value, list) else models.MatchValue(value=value)
            )
            for key, value in fields.items()
        ]
    )


def chunks_only(base: models.Filter | None = None) -> models.Filter:
    condition = models.FieldCondition(key="chunk_index", range=models.Range(gte=0))
    return models.Filter(must=[*(base.must if base else []), condition])


def cosine(left: Sequence[float], right: Sequence[float]) -> float:
    a, b = np.asarray(left, dtype=np.float64), np.asarray(right, dtype=np.float64)
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))


def chunk_points(
    source_id: int, path: str, content_hash: str, chunks: Sequence[StoredChunk]
) -> list[models.PointStruct]:
    shared = {
        "source_id": source_id,
        "path": path,
        "document_id": document_id(source_id, path),
        "content_hash": content_hash,
        "chunk_count": len(chunks),
        "ingested_at": datetime.now(UTC).isoformat(),
    }
    document_point = models.PointStruct(
        id=point_id(source_id, path, DOCUMENT_POINT),
        vector={},
        payload=shared | {"chunk_index": DOCUMENT_POINT},
    )
    return [document_point] + [
        models.PointStruct(
            id=point_id(source_id, path, chunk.index),
            vector={
                "dense": [float(value) for value in chunk.vector],
                "bm25": models.Document(text=chunk.embedding_text, model=BM25_MODEL),
            },
            payload=shared
            | {"chunk_index": chunk.index, "content": chunk.content, "embedding_text": chunk.embedding_text},
        )
        for chunk in chunks
    ]


class QdrantEngine:
    def __init__(self, url: str) -> None:
        # cloud_inference sends the BM25 Documents to the server, which builds the sparse vectors itself.
        self._client = QdrantClient(url=url, cloud_inference=True, timeout=120)

    def create(self, database_id: int, dimensions: int) -> None:
        name = collection_name(database_id)
        if self._client.collection_exists(name):
            return
        self._client.create_collection(
            name,
            vectors_config={"dense": models.VectorParams(size=dimensions, distance=models.Distance.COSINE)},
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        for field, schema in INDEXED_FIELDS.items():
            self._client.create_payload_index(name, field, schema)

    def drop(self, database_id: int) -> None:
        if self._client.collection_exists(collection_name(database_id)):
            self._client.delete_collection(collection_name(database_id))

    def _scroll(self, database_id: int, query_filter: models.Filter, vectors: bool = False) -> Iterator[models.Record]:
        offset = None
        while True:
            records, offset = self._client.scroll(
                collection_name(database_id),
                scroll_filter=query_filter,
                limit=SCROLL_PAGE,
                offset=offset,
                with_payload=True,
                with_vectors=["dense"] if vectors else False,
            )
            yield from records
            if offset is None:
                return

    def document_hashes(self, database_id: int, source_id: int) -> dict[str, str]:
        documents = self._scroll(database_id, matching(source_id=source_id, chunk_index=DOCUMENT_POINT))
        return {record.payload["path"]: record.payload["content_hash"] for record in documents}

    def replace_document(
        self, database_id: int, source_id: int, path: str, content_hash: str, chunks: Sequence[StoredChunk]
    ) -> None:
        self.remove_documents(database_id, source_id, [path])
        self._client.upsert(
            collection_name(database_id), chunk_points(source_id, path, content_hash, chunks), wait=True
        )

    def remove_documents(self, database_id: int, source_id: int, paths: Iterable[str]) -> None:
        paths = list(paths)
        if paths:
            self._client.delete(collection_name(database_id), matching(source_id=source_id, path=paths), wait=True)

    def remove_source(self, database_id: int, source_id: int) -> int:
        name = collection_name(database_id)
        removed = self._client.count(name, matching(source_id=source_id, chunk_index=DOCUMENT_POINT), exact=True).count
        self._client.delete(name, matching(source_id=source_id), wait=True)
        return removed

    def counts(self, database_id: int) -> tuple[int, int]:
        name = collection_name(database_id)
        documents = self._client.count(name, matching(chunk_index=DOCUMENT_POINT), exact=True).count
        return documents, self._client.count(name, chunks_only(), exact=True).count

    def search(self, database_id: int, vector: Sequence[float], text: str, limit: int, mode: str) -> list[SearchHit]:
        name, dense = collection_name(database_id), [float(value) for value in vector]
        if mode != "hybrid":
            points = self._client.query_points(name, query=dense, using="dense", limit=limit, with_payload=True).points
            return [
                self._hit(point, point.score, point.score, rank, None) for rank, point in enumerate(points, start=1)
            ]
        keyword_query = models.Document(text=text, model=BM25_MODEL)
        semantic, keyword = self._client.query_batch_points(
            name,
            [
                models.QueryRequest(query=dense, using="dense", limit=CANDIDATE_POOL),
                models.QueryRequest(query=keyword_query, using="bm25", limit=CANDIDATE_POOL),
            ],
        )
        fused = self._client.query_points(
            name,
            prefetch=[
                models.Prefetch(query=dense, using="dense", limit=CANDIDATE_POOL),
                models.Prefetch(query=keyword_query, using="bm25", limit=CANDIDATE_POOL),
            ],
            query=models.RrfQuery(rrf=models.Rrf(k=RRF_K)),
            limit=limit,
            with_payload=True,
            with_vectors=["dense"],
        ).points
        semantic_ranks = {point.id: rank for rank, point in enumerate(semantic.points, start=1)}
        keyword_ranks = {point.id: rank for rank, point in enumerate(keyword.points, start=1)}
        return [
            self._hit(
                point,
                point.score,
                cosine(dense, point.vector["dense"]),
                semantic_ranks.get(point.id),
                keyword_ranks.get(point.id),
            )
            for point in fused
        ]

    @staticmethod
    def _hit(point, score: float, similarity: float, semantic_rank: int | None, keyword_rank: int | None) -> SearchHit:
        payload = point.payload
        return SearchHit(
            document_id=payload["document_id"],
            source_id=payload["source_id"],
            path=payload["path"],
            chunk_index=payload["chunk_index"],
            content=payload["content"],
            score=float(score),
            similarity=float(similarity),
            semantic_rank=semantic_rank,
            keyword_rank=keyword_rank,
        )

    def documents(self, database_id: int, source_id: int | None, path_contains: str, limit: int) -> list[DocumentInfo]:
        fields = {"chunk_index": DOCUMENT_POINT} | ({"source_id": source_id} if source_id is not None else {})
        needle = path_contains.lower()
        rows = [
            DocumentInfo(
                id=record.payload["document_id"],
                source_id=record.payload["source_id"],
                path=record.payload["path"],
                chunks=record.payload["chunk_count"],
                ingested_at=record.payload["ingested_at"],
            )
            for record in self._scroll(database_id, matching(**fields))
            if needle in record.payload["path"].lower()
        ]
        return sorted(rows, key=lambda row: (row.source_id, row.path))[:limit]

    def chunks(self, database_id: int, document_id: int) -> list[ChunkInfo]:
        records = sorted(
            self._scroll(database_id, chunks_only(matching(document_id=document_id)), vectors=True),
            key=lambda record: record.payload["chunk_index"],
        )
        infos = []
        for record in records:
            vector = record.vector["dense"]
            preview, norm = vector_preview(vector)
            infos.append(
                ChunkInfo(
                    index=record.payload["chunk_index"],
                    content=record.payload["content"],
                    embedding_text=record.payload["embedding_text"],
                    dimensions=len(vector),
                    vector_preview=preview,
                    norm=norm,
                )
            )
        return infos
