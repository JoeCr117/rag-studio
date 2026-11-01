"""Vector engines by name. Adding an engine means one class implementing VectorEngine here."""

from functools import cache

from django.conf import settings

from studio.databases.engines.base import VectorEngine
from studio.databases.engines.pgvector_engine import PgVectorEngine
from studio.databases.engines.qdrant_engine import QdrantEngine

ENGINE_NAMES = ["pgvector", "qdrant"]


@cache
def engine_named(name: str) -> VectorEngine:
    match name:
        case "pgvector":
            return PgVectorEngine(settings.VECTOR_ADMIN_URL)
        case "qdrant":
            return QdrantEngine(settings.QDRANT_URL)
    raise LookupError(f"Unknown vector engine {name!r}")
