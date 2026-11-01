"""Where a database's embedder container answers, for the worker (ingest) and the API (search queries)."""

from studio.databases.catalog import EMBEDDING_MODELS, embedder_name
from studio.ingestion.embedding_client import EmbeddingClient
from studio.models import VectorDatabase


def embedder_url(database: VectorDatabase) -> str:
    return f"http://{embedder_name(database.embedding_model, database.embedder_runtime)}:8080"


def embedder_for(database: VectorDatabase) -> EmbeddingClient:
    return EmbeddingClient(embedder_url(database), EMBEDDING_MODELS[database.embedding_model])
