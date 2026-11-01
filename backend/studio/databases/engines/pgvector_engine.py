"""pgvector: each app database is a Postgres database `vdb_<id>` on the shared pgvector server.

Vectors up to 2,000 dimensions use the `vector` type (32-bit floats). Larger ones use `halfvec` (16-bit floats): an
HNSW index covers at most 2,000 dimensions of `vector` and 4,000 of `halfvec`.
"""

from collections.abc import Iterable, Sequence

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql
from psycopg.conninfo import make_conninfo

from studio.databases.engines.base import ChunkInfo, DocumentInfo, SearchHit, StoredChunk, vector_preview

VECTOR_MAX_DIMENSIONS = 2000
RRF_K = 60
CANDIDATE_POOL = 40


def database_name(database_id: int) -> str:
    return f"vdb_{database_id}"


def column_type(dimensions: int) -> str:
    return "vector" if dimensions <= VECTOR_MAX_DIMENSIONS else "halfvec"


def schema_sql(dimensions: int) -> str:
    kind = column_type(dimensions)
    return f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS documents (
            id bigserial PRIMARY KEY,
            source_id bigint NOT NULL,
            path text NOT NULL,
            content_hash text NOT NULL,
            ingested_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (source_id, path)
        );
        CREATE TABLE IF NOT EXISTS chunks (
            id bigserial PRIMARY KEY,
            document_id bigint NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            chunk_index int NOT NULL,
            content text NOT NULL,
            embedding_text text NOT NULL,
            embedding {kind}({dimensions}) NOT NULL,
            search_vector tsvector GENERATED ALWAYS AS (to_tsvector('english', embedding_text)) STORED
        );
        CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw ON chunks USING hnsw (embedding {kind}_cosine_ops);
        CREATE INDEX IF NOT EXISTS chunks_search_gin ON chunks USING gin (search_vector);
    """


# Both rankings come from the top CANDIDATE_POOL chunks of each method; Reciprocal Rank Fusion adds 1 / (60 + rank)
# from each list a chunk appears in, so agreeing methods win. Keyword terms are OR-ed so one rare word can match.
HYBRID_SQL = """
    WITH semantic AS (
        SELECT id, row_number() OVER (ORDER BY embedding <=> %(vector)s::vector::{kind}) AS rank
        FROM chunks ORDER BY embedding <=> %(vector)s::vector::{kind} LIMIT %(pool)s
    ),
    keyword AS (
        SELECT id, row_number() OVER (ORDER BY ts_rank_cd(search_vector, query) DESC) AS rank
        FROM chunks, to_tsquery('english', replace(plainto_tsquery('english', %(text)s)::text, ' & ', ' | ')) AS query
        WHERE search_vector @@ query
        ORDER BY ts_rank_cd(search_vector, query) DESC LIMIT %(pool)s
    ),
    fused AS (
        SELECT coalesce(s.id, k.id) AS id,
               coalesce(1.0 / (%(rrf_k)s + s.rank), 0) + coalesce(1.0 / (%(rrf_k)s + k.rank), 0) AS score,
               s.rank AS semantic_rank, k.rank AS keyword_rank
        FROM semantic s FULL OUTER JOIN keyword k ON s.id = k.id
    )
    SELECT d.id, d.source_id, d.path, c.chunk_index, c.content, f.score,
           1 - (c.embedding <=> %(vector)s::vector::{kind}), f.semantic_rank, f.keyword_rank
    FROM fused f JOIN chunks c ON c.id = f.id JOIN documents d ON d.id = c.document_id
    ORDER BY f.score DESC LIMIT %(limit)s
"""

VECTOR_SQL = """
    SELECT d.id, d.source_id, d.path, c.chunk_index, c.content,
           1 - (c.embedding <=> %(vector)s::vector::{kind}) AS similarity,
           1 - (c.embedding <=> %(vector)s::vector::{kind}),
           row_number() OVER (ORDER BY c.embedding <=> %(vector)s::vector::{kind}), NULL::bigint
    FROM chunks c JOIN documents d ON d.id = c.document_id
    ORDER BY c.embedding <=> %(vector)s::vector::{kind} LIMIT %(limit)s
"""


class PgVectorEngine:
    def __init__(self, admin_url: str) -> None:
        self._admin_url = admin_url

    def _admin(self) -> psycopg.Connection:
        return psycopg.connect(self._admin_url, autocommit=True)

    def _database(self, database_id: int) -> psycopg.Connection:
        connection = psycopg.connect(make_conninfo(self._admin_url, dbname=database_name(database_id)), autocommit=True)
        register_vector(connection)
        return connection

    def _column_type(self, database_id: int) -> str:
        """Read from the table each time: the worker can rebuild a database with another type while the API runs."""
        with self._database(database_id) as connection:
            row = connection.execute(
                "SELECT t.typname FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid "
                "WHERE a.attrelid = 'chunks'::regclass AND a.attname = 'embedding'"
            ).fetchone()
            return row[0]

    def create(self, database_id: int, dimensions: int) -> None:
        name = database_name(database_id)
        with self._admin() as admin:
            if not admin.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
                admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        with psycopg.connect(make_conninfo(self._admin_url, dbname=name), autocommit=True) as connection:
            connection.execute(schema_sql(dimensions))

    def drop(self, database_id: int) -> None:
        with self._admin() as admin:
            admin.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(database_name(database_id)))
            )

    def document_hashes(self, database_id: int, source_id: int) -> dict[str, str]:
        with self._database(database_id) as connection:
            rows = connection.execute("SELECT path, content_hash FROM documents WHERE source_id = %s", (source_id,))
            return dict(rows.fetchall())

    def replace_document(
        self, database_id: int, source_id: int, path: str, content_hash: str, chunks: Sequence[StoredChunk]
    ) -> None:
        kind = self._column_type(database_id)
        with self._database(database_id) as connection, connection.transaction():
            connection.execute("DELETE FROM documents WHERE source_id = %s AND path = %s", (source_id, path))
            document_id = connection.execute(
                "INSERT INTO documents (source_id, path, content_hash) VALUES (%s, %s, %s) RETURNING id",
                (source_id, path, content_hash),
            ).fetchone()[0]
            with connection.cursor() as cursor:
                cursor.executemany(
                    f"INSERT INTO chunks (document_id, chunk_index, content, embedding_text, embedding) "
                    f"VALUES (%s, %s, %s, %s, %s::vector::{kind})",
                    [
                        (
                            document_id,
                            chunk.index,
                            chunk.content,
                            chunk.embedding_text,
                            np.asarray(chunk.vector, dtype=np.float32),
                        )
                        for chunk in chunks
                    ],
                )

    def remove_documents(self, database_id: int, source_id: int, paths: Iterable[str]) -> None:
        with self._database(database_id) as connection:
            connection.execute(
                "DELETE FROM documents WHERE source_id = %s AND path = ANY(%s)", (source_id, list(paths))
            )

    def remove_source(self, database_id: int, source_id: int) -> int:
        with self._database(database_id) as connection:
            return connection.execute("DELETE FROM documents WHERE source_id = %s", (source_id,)).rowcount

    def counts(self, database_id: int) -> tuple[int, int]:
        with self._database(database_id) as connection:
            documents = connection.execute("SELECT count(*) FROM documents").fetchone()[0]
            chunks = connection.execute("SELECT count(*) FROM chunks").fetchone()[0]
            return documents, chunks

    def search(self, database_id: int, vector: Sequence[float], text: str, limit: int, mode: str) -> list[SearchHit]:
        template = HYBRID_SQL if mode == "hybrid" else VECTOR_SQL
        parameters = {
            "vector": np.asarray(vector, dtype=np.float32),
            "text": text,
            "pool": CANDIDATE_POOL,
            "rrf_k": RRF_K,
            "limit": limit,
        }
        with self._database(database_id) as connection:
            rows = connection.execute(template.format(kind=self._column_type(database_id)), parameters).fetchall()
        return [
            SearchHit(
                document_id=row[0],
                source_id=row[1],
                path=row[2],
                chunk_index=row[3],
                content=row[4],
                score=float(row[5]),
                similarity=float(row[6]),
                semantic_rank=row[7],
                keyword_rank=row[8],
            )
            for row in rows
        ]

    def documents(self, database_id: int, source_id: int | None, path_contains: str, limit: int) -> list[DocumentInfo]:
        with self._database(database_id) as connection:
            rows = connection.execute(
                """SELECT d.id, d.source_id, d.path, count(c.id), d.ingested_at
                   FROM documents d LEFT JOIN chunks c ON c.document_id = d.id
                   WHERE (%(source)s::bigint IS NULL OR d.source_id = %(source)s) AND d.path ILIKE %(pattern)s
                   GROUP BY d.id ORDER BY d.source_id, d.path LIMIT %(limit)s""",
                {"source": source_id, "pattern": f"%{path_contains}%", "limit": limit},
            ).fetchall()
        return [
            DocumentInfo(id=r[0], source_id=r[1], path=r[2], chunks=r[3], ingested_at=r[4].isoformat()) for r in rows
        ]

    def chunks(self, database_id: int, document_id: int) -> list[ChunkInfo]:
        with self._database(database_id) as connection:
            rows = connection.execute(
                "SELECT chunk_index, content, embedding_text, embedding::vector::real[] FROM chunks "
                "WHERE document_id = %s ORDER BY chunk_index",
                (document_id,),
            ).fetchall()
        infos = []
        for index, content, embedding_text, vector in rows:
            preview, norm = vector_preview(vector)
            infos.append(
                ChunkInfo(
                    index=index,
                    content=content,
                    embedding_text=embedding_text,
                    dimensions=len(vector),
                    vector_preview=preview,
                    norm=norm,
                )
            )
        return infos
