"""REST API for the UI. GET /api/state returns everything the page shows; every action is a small POST/PUT/DELETE."""

from dataclasses import asdict
from pathlib import PureWindowsPath

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from loguru import logger
from ninja import NinjaAPI, Schema
from ninja.errors import HttpError

from studio import control_client
from studio.databases.catalog import SEARCH_MODES, embedder_name, form_options, invalid_settings
from studio.databases.engines import ENGINE_NAMES, engine_named
from studio.databases.status import assignment_status, database_warnings
from studio.glossary import glossary_note
from studio.inference.catalog import GENERATOR_CONTEXTS, GENERATOR_MODELS, RERANKER_MODELS, inference_options
from studio.inference.model_server import ModelServerError
from studio.inference.servers import (
    database_start_warning,
    generator_start_warning,
    mark_missing_containers_stopped,
    reranker_start_warning,
    running_vram_gb,
)
from studio.inference.vram import current_vram
from studio.jobs.queue import enqueue
from studio.model_downloads import DOWNLOADABLE_MODELS, delete_download, download_statuses, is_downloaded
from studio.model_locations import model_locations
from studio.models import Assignment, InferenceServer, Job, Source, VectorDatabase
from studio.runtimes import NO_GPU_MESSAGE, RUNTIMES, available_runtimes
from studio.search.answering import answer_question
from studio.search.context_budget import QuestionTooLong
from studio.search.querying import result_view, search_database
from studio.sources.host_paths import InvalidHostPath, container_path

api = NinjaAPI(title="RAG Studio")
RECENT_JOBS = 25
MAX_SEARCH_RESULTS = 50
MAX_RERANK_POOL = 100
DOCUMENT_PAGE = 500
VRAM_WARNING = 409
"""Status for "this GPU start probably does not fit"; the UI offers Start anyway, which resends with force=true."""
SERVER_JOBS = {
    InferenceServer.Role.GENERATOR: (Job.Kind.START_GENERATOR, Job.Kind.STOP_GENERATOR),
    InferenceServer.Role.RERANKER: (Job.Kind.START_RERANKER, Job.Kind.STOP_RERANKER),
}


@api.exception_handler(ModelServerError)
def model_server_error(request, error: ModelServerError):
    logger.error("{} {} failed: {}", request.method, request.path, error)
    return api.create_response(request, {"detail": str(error)}, status=502)


@api.exception_handler(Exception)
def unexpected_error(request, error: Exception):
    logger.opt(exception=error).error("{} {} failed: {}", request.method, request.path, error)
    return api.create_response(request, {"detail": f"Server error: {error}"}, status=500)


class SourceIn(Schema):
    name: str = ""
    host_path: str
    include_patterns: str = ""
    exclude_patterns: str = ""


class SourcePatternsIn(Schema):
    include_patterns: str = ""
    exclude_patterns: str = ""


class SearchIn(Schema):
    query: str
    limit: int = 8
    mode: str = ""
    """Empty means the database's own search mode."""
    rerank_pool: int | None = None
    """Candidates handed to the reranker; None searches without reranking."""


class AskIn(SearchIn):
    think: bool = False
    """Let the generator write its reasoning before answering."""


class ServerStartIn(Schema):
    model_key: str
    runtime: str = "cpu"
    context: int = 8192
    force: bool = False


class DatabaseIn(Schema):
    name: str
    engine: str
    embedding_model: str
    embedder_runtime: str
    chunk_min_tokens: int
    chunk_max_tokens: int
    chunk_overlap_tokens: int
    search_mode: str


def _iso(value) -> str | None:
    return value.isoformat() if value else None


def _status(assignment: Assignment) -> str:
    source = assignment.source
    return assignment_status(assignment.connected, source.found, source.fingerprint, assignment.synced_fingerprint)


def _source_view(source: Source) -> dict:
    return {
        "id": source.id,
        "name": source.name,
        "host_path": source.host_path,
        "include_patterns": source.include_patterns,
        "exclude_patterns": source.exclude_patterns,
        "found": source.found,
        "file_count": source.file_count,
        "scanned_at": _iso(source.scanned_at),
        "scan_error": source.scan_error,
        "assignments": [
            {
                "database_id": assignment.database_id,
                "database_name": assignment.database.name,
                "status": _status(assignment),
            }
            for assignment in source.assignments.all()
        ],
    }


def _counts(database: VectorDatabase) -> dict | None:
    if database.built_with is None:
        return None
    try:
        documents, chunks = engine_named(database.engine).counts(database.id)
    except Exception:
        return None
    return {"documents": documents, "chunks": chunks}


def _database_view(database: VectorDatabase, busy_ids: set[int]) -> dict:
    assignments = list(database.assignments.all())
    statuses = [_status(assignment) for assignment in assignments]
    return {
        "id": database.id,
        "name": database.name,
        "engine": database.engine,
        "embedding_model": database.embedding_model,
        "embedder_runtime": database.embedder_runtime,
        "embedder": embedder_name(database.embedding_model, database.embedder_runtime),
        "chunk_min_tokens": database.chunk_min_tokens,
        "chunk_max_tokens": database.chunk_max_tokens,
        "chunk_overlap_tokens": database.chunk_overlap_tokens,
        "search_mode": database.search_mode,
        "running": database.running,
        "ready": database.built_with is not None,
        "needs_rebuild": database.needs_rebuild,
        "busy": database.id in busy_ids,
        "counts": _counts(database),
        "warnings": database_warnings(database.needs_rebuild, statuses),
        "assignments": [
            {
                "source_id": assignment.source_id,
                "source_name": assignment.source.name,
                "connected": assignment.connected,
                "status": status,
                "synced_at": _iso(assignment.synced_at),
            }
            for assignment, status in zip(assignments, statuses, strict=True)
        ],
    }


def _progress_view(job: Job) -> dict | None:
    if job.status != Job.Status.RUNNING or job.progress_done is None:
        return None
    return {
        "done": job.progress_done,
        "total": job.progress_total,
        "unit": job.progress_unit,
        "detail": job.progress_detail,
    }


def _job_view(job: Job) -> dict:
    return {
        "id": job.id,
        "kind": job.kind,
        "status": job.status,
        "title": job.title,
        "message": job.message,
        "database_id": job.database_id,
        "source_id": job.source_id,
        "model_key": job.model_key,
        "progress": _progress_view(job),
        "created_at": _iso(job.created_at),
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
    }


def _recent_jobs() -> list[Job]:
    """The newest jobs, plus the running one even when a long queue has pushed it out of that window."""
    recent = list(Job.objects.order_by("-id")[:RECENT_JOBS])
    running = Job.objects.filter(status=Job.Status.RUNNING).exclude(pk__in=[job.pk for job in recent])
    return recent + list(running)


@api.get("/health")
def health(request):
    return {"ok": True}


@api.get("/glossary/{name}")
def glossary(request, name: str):
    note = glossary_note(settings.GLOSSARY_VAULT_DIR, name)
    if note is None:
        raise HttpError(404, f"No vault note named {name!r}")
    return asdict(note)


@api.get("/state")
def state(request):
    sources = list(Source.objects.prefetch_related("assignments__database").order_by("name"))
    active = Job.objects.filter(status__in=[Job.Status.QUEUED, Job.Status.RUNNING])
    busy_ids = set(active.exclude(database=None).values_list("database_id", flat=True))
    databases = VectorDatabase.objects.prefetch_related("assignments__source").order_by("name")
    statuses = download_statuses(set(active.exclude(model_key="").values_list("model_key", flat=True)))
    return {
        "sources": [_source_view(source) for source in sources],
        "databases": [_database_view(database, busy_ids) for database in databases],
        "jobs": [_job_view(job) for job in _recent_jobs()],
        "model_locations": model_locations(),
        "servers": _server_views(active),
        "gpu_available": settings.GPU_AVAILABLE,
        "vram": _vram_view(),
        "options": form_options(ENGINE_NAMES, statuses, _runtimes()) | inference_options(statuses),
    }


def _runtimes() -> tuple[str, ...]:
    return available_runtimes(settings.GPU_AVAILABLE)


def _refuse_if_no_gpu(runtime: str) -> None:
    if runtime in RUNTIMES and runtime not in _runtimes():
        raise HttpError(400, NO_GPU_MESSAGE)


def _vram_view() -> dict | None:
    usage = current_vram()
    return None if usage is None else {"used_mib": usage.used_mib, "total_mib": usage.total_mib}


def _server_views(active_jobs) -> dict:
    rows = {server.role: server for server in InferenceServer.objects.all()}
    busy_kinds = set(active_jobs.values_list("kind", flat=True))
    return {
        role.value: {
            "model_key": rows[role].model_key if role in rows else None,
            "runtime": rows[role].runtime if role in rows else None,
            "context": rows[role].context if role in rows else None,
            "running": role in rows and rows[role].running,
            "busy": bool(busy_kinds & set(SERVER_JOBS[role])),
            "vram_gb": running_vram_gb(rows.get(role)),
        }
        for role in InferenceServer.Role
    }


def _source(source_id: int) -> Source:
    source = Source.objects.filter(pk=source_id).first()
    if source is None:
        raise HttpError(404, f"No source {source_id}")
    return source


def _database(database_id: int) -> VectorDatabase:
    database = VectorDatabase.objects.filter(pk=database_id).first()
    if database is None:
        raise HttpError(404, f"No database {database_id}")
    return database


def _queue_once(kind: Job.Kind, title: str, database: VectorDatabase, source: Source | None = None) -> dict:
    """Pressing a button twice queues the job once."""
    existing = Job.objects.filter(kind=kind, database=database, source=source, status=Job.Status.QUEUED).first()
    return _job_view(existing or enqueue(kind, title, database, source))


@api.post("/sources")
def register_source(request, payload: SourceIn):
    host_path = payload.host_path.strip().strip('"')
    if Source.objects.filter(host_path__iexact=host_path).exists():
        raise HttpError(400, f"{host_path} is already registered")
    name = payload.name.strip() or PureWindowsPath(host_path).name or host_path
    if Source.objects.filter(name=name).exists():
        raise HttpError(400, f"A source named '{name}' already exists")
    try:
        container_path(host_path, settings.HOST_DRIVES_ROOT)
    except InvalidHostPath as error:
        raise HttpError(400, str(error)) from error
    try:
        control_client.check_source(host_path)
    except control_client.ControlError as error:
        raise HttpError(400, str(error)) from error
    source = Source.objects.create(
        name=name,
        host_path=host_path,
        include_patterns=payload.include_patterns,
        exclude_patterns=payload.exclude_patterns,
    )
    logger.info("Registered source '{}' ({})", name, host_path)
    return _source_view(source)


@api.put("/sources/{source_id}/patterns")
def update_patterns(request, source_id: int, payload: SourcePatternsIn):
    source = _source(source_id)
    source.include_patterns, source.exclude_patterns = payload.include_patterns, payload.exclude_patterns
    source.save(update_fields=["include_patterns", "exclude_patterns"])
    logger.info("Updated file patterns of '{}'", source.name)
    return _source_view(source)


@api.delete("/sources/{source_id}")
def unregister_source(request, source_id: int):
    source = _source(source_id)
    if source.assignments.exists():
        names = ", ".join(source.assignments.values_list("database__name", flat=True))
        raise HttpError(400, f"'{source.name}' still feeds {names}: disconnect it and Sync all there first")
    source.delete()
    logger.info("Unregistered source '{}'", source.name)
    return {"ok": True}


def _checked_settings(payload: DatabaseIn) -> dict:
    values = payload.dict()
    values["name"] = values["name"].strip()
    if not values["name"]:
        raise HttpError(400, "A database needs a name")
    _refuse_if_no_gpu(values["embedder_runtime"])
    problems = invalid_settings(values, ENGINE_NAMES, _runtimes())
    if problems:
        raise HttpError(400, "Invalid settings: " + "; ".join(problems))
    return values


@api.post("/databases")
def create_database(request, payload: DatabaseIn):
    values = _checked_settings(payload)
    if VectorDatabase.objects.filter(name=values["name"]).exists():
        raise HttpError(400, f"A database named '{values['name']}' already exists")
    database = VectorDatabase.objects.create(**values)
    enqueue(Job.Kind.CREATE, f"Create database '{database.name}'", database)
    return _database_view(database, set())


@api.put("/databases/{database_id}")
def update_database(request, database_id: int, payload: DatabaseIn):
    database = _database(database_id)
    values = _checked_settings(payload)
    if VectorDatabase.objects.filter(name=values["name"]).exclude(pk=database.pk).exists():
        raise HttpError(400, f"A database named '{values['name']}' already exists")
    embedder_changes = (values["embedding_model"], values["embedder_runtime"]) != (
        database.embedding_model,
        database.embedder_runtime,
    )
    if database.running and embedder_changes:
        raise HttpError(400, "Stop the database before changing its embedding model or runtime")
    for field, value in values.items():
        setattr(database, field, value)
    database.save()
    logger.info("Updated settings of '{}'{}", database.name, ": needs a rebuild" if database.needs_rebuild else "")
    return _database_view(database, set())


@api.delete("/databases/{database_id}")
def delete_database(request, database_id: int):
    database = _database(database_id)
    return _queue_once(Job.Kind.DELETE, f"Delete database '{database.name}'", database)


def _refuse_if_vram_short(warning: str | None, force: bool) -> None:
    if warning and not force:
        raise HttpError(VRAM_WARNING, warning)
    if warning:
        logger.warning("Starting despite the VRAM warning: {}", warning)


@api.post("/shutdown")
def shutdown(request):
    """Stops every RAG Studio container, this API included; databases, models and settings stay in their volumes."""
    cancelled = Job.objects.filter(status=Job.Status.QUEUED).update(
        status=Job.Status.FAILED,
        message="Cancelled: RAG Studio shut down",
        finished_at=timezone.now(),
    )
    stopped = mark_missing_containers_stopped(set())
    logger.warning(
        "Shutting down RAG Studio: {} queued job(s) cancelled, stopping {}",
        cancelled,
        ", ".join(stopped) or "no running services",
    )
    try:
        result = control_client.shutdown()
    except control_client.ControlError as error:
        raise HttpError(400, str(error)) from error
    logger.warning("Shutdown: {}", result)
    return {"ok": True, "result": result}


@api.post("/databases/{database_id}/start")
def start_database(request, database_id: int, force: bool = False):
    database = _database(database_id)
    _refuse_if_no_gpu(database.embedder_runtime)
    _refuse_if_vram_short(database_start_warning(database), force)
    return _queue_once(Job.Kind.START, f"Start database '{database.name}'", database)


def _role(name: str) -> InferenceServer.Role:
    if name not in InferenceServer.Role.values:
        raise HttpError(404, f"No server role {name!r}")
    return InferenceServer.Role(name)


@api.post("/servers/{role}/start")
def start_server(request, role: str, payload: ServerStartIn):
    role = _role(role)
    catalog = GENERATOR_MODELS if role == InferenceServer.Role.GENERATOR else RERANKER_MODELS
    model = catalog.get(payload.model_key)
    if model is None:
        raise HttpError(400, f"No {role.value} model {payload.model_key!r} in the catalog")
    runtime = payload.runtime
    _refuse_if_no_gpu(runtime)
    if runtime not in _runtimes() or payload.context not in GENERATOR_CONTEXTS:
        raise HttpError(400, f"Runtime must be one of {_runtimes()} and context one of {GENERATOR_CONTEXTS}")
    if Job.objects.filter(kind__in=SERVER_JOBS[role], status__in=[Job.Status.QUEUED, Job.Status.RUNNING]).exists():
        raise HttpError(400, f"The {role.value} is already starting or stopping")
    warning = (
        generator_start_warning(payload.model_key, runtime, payload.context)
        if role == InferenceServer.Role.GENERATOR
        else reranker_start_warning(payload.model_key, runtime)
    )
    _refuse_if_vram_short(warning, payload.force)
    InferenceServer.objects.update_or_create(
        role=role,
        defaults={"model_key": payload.model_key, "runtime": runtime, "context": payload.context},
    )
    detail = (
        f"{runtime.upper()}, {payload.context:,}-token context"
        if role == InferenceServer.Role.GENERATOR
        else runtime.upper()
    )
    return _job_view(enqueue(SERVER_JOBS[role][0], f"Start {role.value} {model.label} ({detail})"))


@api.post("/servers/{role}/stop")
def stop_server(request, role: str):
    role = _role(role)
    return _job_view(enqueue(SERVER_JOBS[role][1], f"Stop {role.value}"))


@api.post("/databases/{database_id}/stop")
def stop_database(request, database_id: int):
    database = _database(database_id)
    return _queue_once(Job.Kind.STOP, f"Stop database '{database.name}'", database)


@api.post("/databases/{database_id}/sync-all")
def sync_all(request, database_id: int):
    database = _database(database_id)
    return _queue_once(Job.Kind.SYNC_ALL, f"Sync all sources into '{database.name}'", database)


@api.post("/databases/{database_id}/sources/{source_id}/connect")
def connect_source(request, database_id: int, source_id: int):
    database, source = _database(database_id), _source(source_id)
    assignment, _ = Assignment.objects.get_or_create(database=database, source=source)
    if not assignment.connected:
        assignment.connected = True
        assignment.save(update_fields=["connected"])
    logger.info("Connected '{}' to '{}'", source.name, database.name)
    return {"ok": True}


@api.post("/databases/{database_id}/sources/{source_id}/disconnect")
def disconnect_source(request, database_id: int, source_id: int):
    assignment = (
        Assignment.objects.filter(database_id=database_id, source_id=source_id)
        .select_related("database", "source")
        .first()
    )
    if assignment is None:
        raise HttpError(404, "That source is not assigned to that database")
    assignment.connected = False
    assignment.save(update_fields=["connected"])
    logger.info(
        "Disconnected '{}' from '{}': its chunks stay until Sync all", assignment.source.name, assignment.database.name
    )
    return {"ok": True}


@api.post("/models/{model_key}/download")
def download_model(request, model_key: str):
    model = DOWNLOADABLE_MODELS.get(model_key)
    if model is None:
        raise HttpError(404, f"No model {model_key!r} in the catalog")
    if is_downloaded(model):
        return {"ok": True, "already": True}
    active = Job.objects.filter(
        kind=Job.Kind.DOWNLOAD, model_key=model_key, status__in=[Job.Status.QUEUED, Job.Status.RUNNING]
    )
    job = active.first() or enqueue(Job.Kind.DOWNLOAD, f"Download {model.label}", model_key=model_key)
    return _job_view(job)


def _why_model_is_busy(model_key: str) -> str | None:
    """Why deleting the model now could break something; None when nothing can be using or fetching it."""
    database = VectorDatabase.objects.filter(embedding_model=model_key, running=True).first()
    if database:
        return f"database '{database.name}' is running on it: stop the database first"
    server = InferenceServer.objects.filter(model_key=model_key, running=True).first()
    if server:
        return f"the {server.role} is running it: stop the {server.role} first"
    if Job.objects.filter(status__in=[Job.Status.QUEUED, Job.Status.RUNNING]).exists():
        return "a job is queued or running and may load or download it: wait for the jobs to finish"
    return None


@api.delete("/models/{model_key}")
def delete_model(request, model_key: str):
    model = DOWNLOADABLE_MODELS.get(model_key)
    if model is None:
        raise HttpError(404, f"No model {model_key!r} in the catalog")
    busy = _why_model_is_busy(model_key)
    if busy:
        raise HttpError(400, f"Cannot delete {model.label}: {busy}")
    return {"ok": True, "freed_gb": round(delete_download(model) / 1e9, 2)}


def _source_names() -> dict[int, str]:
    return dict(Source.objects.values_list("id", "name"))


def _server_running(role: InferenceServer.Role) -> bool:
    return InferenceServer.objects.filter(role=role, running=True).exists()


def _checked_search(database: VectorDatabase, payload: SearchIn) -> tuple[str, str, int, int | None]:
    """(query, mode, limit, rerank_pool) once the database and the reranker, if asked for, can serve the search."""
    if not database.running:
        raise HttpError(400, f"Start '{database.name}' first: its embedder turns the query into a vector")
    if database.needs_rebuild:
        raise HttpError(400, f"'{database.name}' needs a rebuild: its stored vectors were made with other settings")
    query, mode = payload.query.strip(), payload.mode or database.search_mode
    if mode not in SEARCH_MODES or not query:
        raise HttpError(400, "A search needs a query and a mode of hybrid or vector")
    if payload.rerank_pool is not None and not _server_running(InferenceServer.Role.RERANKER):
        raise HttpError(400, "Start the reranker on the Ask tab first")
    limit = max(1, min(payload.limit, MAX_SEARCH_RESULTS))
    pool = None if payload.rerank_pool is None else max(limit, min(payload.rerank_pool, MAX_RERANK_POOL))
    return query, mode, limit, pool


@api.post("/databases/{database_id}/search")
def search(request, database_id: int, payload: SearchIn):
    database = _database(database_id)
    query, mode, limit, pool = _checked_search(database, payload)
    result = search_database(database, query, limit, mode, pool)
    reranking = f", reranked from {pool}" if pool else ""
    logger.info("Search '{}' in '{}' ({}{}): {} hits", query[:60], database.name, mode, reranking, len(result.hits))
    return result_view(result, _source_names())


@api.post("/databases/{database_id}/ask")
def ask(request, database_id: int, payload: AskIn):
    database = _database(database_id)
    query, mode, limit, pool = _checked_search(database, payload)
    if not _server_running(InferenceServer.Role.GENERATOR):
        raise HttpError(400, "Start a generator first")
    names = _source_names()
    window = InferenceServer.objects.get(role=InferenceServer.Role.GENERATOR).context
    try:
        answer = answer_question(database, query, limit, mode, pool, names, window, payload.think)
    except QuestionTooLong as error:
        raise HttpError(400, str(error)) from error
    completion, budget = answer.completion, answer.budget
    logger.info(
        "Ask '{}' in '{}'{}: {} of {} passages fit, {} prompt tokens, {} output tokens at {} tok/s{}",
        query[:60],
        database.name,
        " with thinking" if payload.think else "",
        budget.passages_used,
        budget.passages_found,
        completion.prompt_tokens,
        completion.completion_tokens,
        completion.tokens_per_second,
        ", cut off at the output allowance" if completion.finish_reason == "length" else "",
    )
    return {
        "answer": answer.text,
        "think": payload.think,
        "completion": asdict(completion),
        "context": asdict(budget) | {"passages_left_out": budget.passages_left_out},
        "search": result_view(answer.search, names),
    }


@api.get("/databases/{database_id}/documents")
def documents(request, database_id: int, source_id: int | None = None, path: str = ""):
    database = _database(database_id)
    if database.built_with is None:
        return {"documents": []}
    names = _source_names()
    rows = engine_named(database.engine).documents(database.id, source_id, path, DOCUMENT_PAGE)
    return {
        "documents": [
            {
                "id": row.id,
                "source_id": row.source_id,
                "source_name": names.get(row.source_id, f"source {row.source_id}"),
                "path": row.path,
                "chunks": row.chunks,
                "ingested_at": row.ingested_at,
            }
            for row in rows
        ],
        "limit": DOCUMENT_PAGE,
    }


@api.get("/databases/{database_id}/documents/{document_id}/chunks")
def chunks(request, database_id: int, document_id: int):
    database = _database(database_id)
    return {"chunks": [chunk.__dict__ for chunk in engine_named(database.engine).chunks(database.id, document_id)]}


@api.post("/databases/{database_id}/sources/{source_id}/sync")
def sync_source(request, database_id: int, source_id: int):
    database, source = _database(database_id), _source(source_id)
    if not Assignment.objects.filter(Q(database=database) & Q(source=source) & Q(connected=True)).exists():
        raise HttpError(400, f"'{source.name}' is not connected to '{database.name}'")
    return _queue_once(Job.Kind.SYNC_SOURCE, f"Sync '{source.name}' into '{database.name}'", database, source)
