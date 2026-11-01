"""The shared generator and reranker, and the VRAM check every GPU start goes through (embedders included)."""

from studio.databases.catalog import EMBEDDING_MODELS, EmbeddingModel, embedder_name
from studio.inference.catalog import GENERATOR_MODELS, RERANKER_MODELS
from studio.inference.vram import current_vram, vram_shortfall
from studio.models import InferenceServer, VectorDatabase

EMBEDDER_BUFFER_GB = 0.6
"""Compute buffers for the embedder's 2,048-token batches, on top of the weights."""


def embedder_vram_gb(model: EmbeddingModel) -> float:
    return round(model.size_gb + EMBEDDER_BUFFER_GB, 1)


def mark_missing_containers_stopped(running_containers: set[str]) -> list[str]:
    """Clears the running flag of every database and server whose container is not in `running_containers`, so the
    UI never shows a dead container as running; returns what was marked stopped."""
    stale_databases = [
        database
        for database in VectorDatabase.objects.filter(running=True)
        if embedder_name(database.embedding_model, database.embedder_runtime) not in running_containers
    ]
    stale_servers = [
        server for server in InferenceServer.objects.filter(running=True) if server.role not in running_containers
    ]
    VectorDatabase.objects.filter(pk__in=[database.pk for database in stale_databases]).update(running=False)
    InferenceServer.objects.filter(pk__in=[server.pk for server in stale_servers]).update(running=False)
    return [database.name for database in stale_databases] + [server.role for server in stale_servers]


def server(role: InferenceServer.Role) -> InferenceServer | None:
    return InferenceServer.objects.filter(role=role).first()


def running_vram_gb(current: InferenceServer | None) -> float:
    """What the server's current container holds on the GPU; zero when stopped or on the CPU."""
    if current is None or not current.running or current.runtime != "gpu":
        return 0.0
    if current.role == InferenceServer.Role.GENERATOR:
        return GENERATOR_MODELS[current.model_key].vram_estimate_gb(current.context)
    return RERANKER_MODELS[current.model_key].vram_gb


def generator_start_warning(model_key: str, runtime: str, context: int) -> str | None:
    """Starting a generator replaces the running one, so its VRAM counts as freed."""
    if runtime != "gpu":
        return None
    need = GENERATOR_MODELS[model_key].vram_estimate_gb(context)
    return vram_shortfall(need, running_vram_gb(server(InferenceServer.Role.GENERATOR)), current_vram())


def reranker_start_warning(model_key: str, runtime: str) -> str | None:
    if runtime != "gpu":
        return None
    need = RERANKER_MODELS[model_key].vram_gb
    return vram_shortfall(need, running_vram_gb(server(InferenceServer.Role.RERANKER)), current_vram())


def database_start_warning(database: VectorDatabase) -> str | None:
    """Only a GPU embedder that is not already running for another database needs new VRAM."""
    if database.embedder_runtime != "gpu":
        return None
    name = embedder_name(database.embedding_model, database.embedder_runtime)
    shared = any(
        embedder_name(other.embedding_model, other.embedder_runtime) == name
        for other in VectorDatabase.objects.filter(running=True).exclude(pk=database.pk)
    )
    if shared:
        return None
    return vram_shortfall(embedder_vram_gb(EMBEDDING_MODELS[database.embedding_model]), 0.0, current_vram())
