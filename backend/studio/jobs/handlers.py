"""What each job kind does. Every handler takes the job and returns a short result message."""

import time
from dataclasses import replace
from pathlib import Path

from django.utils import timezone
from loguru import logger

from studio import control_client
from studio.databases.catalog import EMBEDDING_MODELS, embedder_name
from studio.databases.embedders import embedder_for, embedder_url
from studio.databases.engines import engine_named
from studio.inference.catalog import GENERATOR_MODELS, RERANKER_MODELS
from studio.inference.clients import GENERATOR_URL, RERANKER_URL, is_healthy
from studio.inference.vram import current_vram
from studio.ingestion.sync import splitters_for, sync_source
from studio.jobs.progress import Progress, ProgressReport, throttled_job_progress
from studio.jobs.queue import JobRefused
from studio.model_downloads import DOWNLOADABLE_MODELS, ModelFile, ensure_downloaded, is_downloaded
from studio.models import Assignment, InferenceServer, Job, VectorDatabase
from studio.sources.scanning import pattern_lines, scan_source

EMBEDDER_START_SECONDS = 180
SERVER_START_SECONDS = 600
"""A large generator spends minutes reading its GGUF through Docker Desktop's file bridge on first load."""
VRAM_SETTLE_SECONDS = 2
"""The driver frees a removed container's memory shortly after it exits."""


def _wait_until_healthy(is_ready, name: str, seconds: int) -> None:
    deadline = time.monotonic() + seconds
    while not is_ready():
        if time.monotonic() > deadline:
            raise RuntimeError(f"{name} did not become healthy within {seconds}s")
        time.sleep(1)


def _vram_used_gb() -> float | None:
    usage = current_vram()
    return usage.used_mib / 1024 if usage else None


def _measured_vram(before: float | None, estimate_gb: float) -> str:
    time.sleep(VRAM_SETTLE_SECONDS)
    after = _vram_used_gb()
    if before is None or after is None:
        return ""
    return f", VRAM +{after - before:.1f} GB (estimated {estimate_gb:.1f})"


def _ensure_model(job: Job, model: ModelFile) -> Path:
    """Tags the job with the model it downloads, so the Models tab shows the download under that model."""
    if not is_downloaded(model):
        Job.objects.filter(pk=job.pk).update(model_key=model.key)
    return ensure_downloaded(model, throttled_job_progress(job))


def create(job: Job) -> str:
    database = job.database
    model = EMBEDDING_MODELS[database.embedding_model]
    engine_named(database.engine).create(database.id, model.dimensions)
    database.built_with = database.vector_settings()
    database.save(update_fields=["built_with"])
    return f"{database.engine} database ready ({model.dimensions} dimensions)"


def start(job: Job) -> str:
    database = job.database
    model = EMBEDDING_MODELS[database.embedding_model]
    _ensure_model(job, model)
    name = embedder_name(database.embedding_model, database.embedder_runtime)
    logger.info(
        "Embedder {}: {}",
        name,
        control_client.start_embedder(name, database.embedder_runtime, model.file, model.pooling),
    )
    _wait_until_healthy(lambda: is_healthy(embedder_url(database)), f"Embedder {name}", EMBEDDER_START_SECONDS)
    database.running = True
    database.save(update_fields=["running"])
    return f"embedder {name} ready"


def _stop_embedder_if_unused(database: VectorDatabase) -> None:
    name = embedder_name(database.embedding_model, database.embedder_runtime)
    sharing = [
        other
        for other in VectorDatabase.objects.filter(running=True).exclude(pk=database.pk)
        if embedder_name(other.embedding_model, other.embedder_runtime) == name
    ]
    if sharing:
        logger.info("Embedder {} kept: still used by {}", name, ", ".join(other.name for other in sharing))
    else:
        control_client.stop_container(name)
        logger.info("Embedder {} stopped", name)


def stop(job: Job) -> str:
    database = job.database
    database.running = False
    database.save(update_fields=["running"])
    _stop_embedder_if_unused(database)
    return "stopped"


def _require_running(database: VectorDatabase) -> None:
    if not database.running:
        raise JobRefused(f"Database '{database.name}' is stopped: start it first")


def _labelled(on_progress: ProgressReport, label: str) -> ProgressReport:
    """Prefixes each progress detail, so Sync all says which source the current file belongs to."""
    return lambda progress: on_progress(replace(progress, detail=f"{label} · {progress.detail}"))


def _sync_assignment(database: VectorDatabase, assignment: Assignment, on_progress: ProgressReport) -> str:
    source = assignment.source
    if not source.container_path.is_dir():
        raise JobRefused(f"Source '{source.name}' folder was not found at {source.host_path}")
    scan = scan_source(
        source.container_path, pattern_lines(source.include_patterns), pattern_lines(source.exclude_patterns)
    )
    logger.info("Syncing '{}' into '{}': {} files", source.name, database.name, len(scan.files))
    with embedder_for(database) as embedder:
        summary = sync_source(
            database.id,
            source.id,
            source.name,
            source.container_path,
            scan,
            engine_named(database.engine),
            embedder,
            splitters_for(
                EMBEDDING_MODELS[database.embedding_model].tokenizer,
                database.chunk_min_tokens,
                database.chunk_max_tokens,
                database.chunk_overlap_tokens,
            ),
            on_progress,
        )
    assignment.synced_fingerprint, assignment.synced_at = scan.fingerprint, timezone.now()
    assignment.save(update_fields=["synced_fingerprint", "synced_at"])
    return (
        f"+{summary.added} ~{summary.updated} ={summary.unchanged} -{summary.removed}, {summary.chunks} chunks embedded"
    )


def sync_one(job: Job) -> str:
    database = job.database
    _require_running(database)
    if database.needs_rebuild:
        raise JobRefused(f"Database '{database.name}' needs a rebuild: use Sync all")
    assignment = Assignment.objects.select_related("source").get(database=database, source=job.source)
    if not assignment.connected:
        raise JobRefused(f"Source '{job.source.name}' is disconnected from '{database.name}'")
    return _sync_assignment(database, assignment, _labelled(throttled_job_progress(job), job.source.name))


def sync_all(job: Job) -> str:
    """Rebuilds if the vector settings changed, removes disconnected sources, then syncs every connected source."""
    database = job.database
    _require_running(database)
    engine = engine_named(database.engine)
    on_progress = throttled_job_progress(job)
    if database.needs_rebuild:
        on_progress(Progress(done=0, total=None, unit="files", detail="Rebuilding: emptying the database"))
        logger.info("Rebuilding '{}': settings changed since its vectors were made", database.name)
        engine.drop(database.id)
        create(job)
        database.assignments.update(synced_fingerprint="", synced_at=None)
    for assignment in database.assignments.select_related("source").filter(connected=False):
        on_progress(
            Progress(done=0, total=None, unit="files", detail=f"Removing disconnected source {assignment.source.name}")
        )
        removed = engine.remove_source(database.id, assignment.source_id)
        logger.info(
            "Removed disconnected source '{}' from '{}' ({} documents)", assignment.source.name, database.name, removed
        )
        assignment.delete()
    connected = list(database.assignments.select_related("source").filter(connected=True))
    results = [
        f"{assignment.source.name}: "
        + _sync_assignment(
            database, assignment, _labelled(on_progress, f"{assignment.source.name} ({number} of {len(connected)})")
        )
        for number, assignment in enumerate(connected, start=1)
    ]
    return "; ".join(results) or "no connected sources"


def delete(job: Job) -> str:
    database = job.database
    if database.running:
        database.running = False
        database.save(update_fields=["running"])
        _stop_embedder_if_unused(database)
    engine_named(database.engine).drop(database.id)
    name = database.name
    database.delete()
    return f"deleted '{name}'"


def download(job: Job) -> str:
    model = DOWNLOADABLE_MODELS[job.model_key]
    path = _ensure_model(job, model)
    return f"{model.file} ready ({path.stat().st_size / 1e9:.2f} GB)"


def _start_server(role: InferenceServer.Role, start_container, url: str, estimate_gb: float) -> str:
    """Stops the previous container first so the VRAM measurement covers only the new model, and removes a container
    that never became healthy so a failed start does not keep holding VRAM."""
    server = InferenceServer.objects.get(role=role)
    server.running = False
    server.save(update_fields=["running"])
    control_client.stop_container(role.value)
    time.sleep(VRAM_SETTLE_SECONDS)
    before = _vram_used_gb()
    logger.info("{}: {}", role.label, start_container())
    try:
        _wait_until_healthy(lambda: is_healthy(url), role.label, SERVER_START_SECONDS)
    except Exception:
        control_client.stop_container(role.value)
        raise
    server.running = True
    server.save(update_fields=["running"])
    return f"{server.model_key} ready on {server.runtime.upper()}" + (
        _measured_vram(before, estimate_gb) if server.runtime == "gpu" else ""
    )


def start_generator(job: Job) -> str:
    server = InferenceServer.objects.get(role=InferenceServer.Role.GENERATOR)
    model = GENERATOR_MODELS[server.model_key]
    _ensure_model(job, model)
    return _start_server(
        InferenceServer.Role.GENERATOR,
        lambda: control_client.start_generator(server.runtime, model.file, server.context, model.cpu_moe_layers),
        GENERATOR_URL,
        model.vram_estimate_gb(server.context),
    )


def start_reranker(job: Job) -> str:
    server = InferenceServer.objects.get(role=InferenceServer.Role.RERANKER)
    model = RERANKER_MODELS[server.model_key]
    _ensure_model(job, model)
    return _start_server(
        InferenceServer.Role.RERANKER,
        lambda: control_client.start_reranker(server.runtime, model.file),
        RERANKER_URL,
        model.vram_gb,
    )


def _stop_server(role: InferenceServer.Role) -> str:
    InferenceServer.objects.filter(role=role).update(running=False)
    control_client.stop_container(role.value)
    return "stopped"


HANDLERS = {
    Job.Kind.DOWNLOAD: download,
    Job.Kind.START_GENERATOR: start_generator,
    Job.Kind.STOP_GENERATOR: lambda job: _stop_server(InferenceServer.Role.GENERATOR),
    Job.Kind.START_RERANKER: start_reranker,
    Job.Kind.STOP_RERANKER: lambda job: _stop_server(InferenceServer.Role.RERANKER),
    Job.Kind.CREATE: create,
    Job.Kind.START: start,
    Job.Kind.STOP: stop,
    Job.Kind.SYNC_SOURCE: sync_one,
    Job.Kind.SYNC_ALL: sync_all,
    Job.Kind.DELETE: delete,
}


def handle(job: Job) -> str:
    return HANDLERS[Job.Kind(job.kind)](job)
