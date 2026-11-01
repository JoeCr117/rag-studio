from pathlib import Path

from django.conf import settings
from django.db import models

from studio.sources.host_paths import container_path


class Source(models.Model):
    """A registered folder on the host, read through the worker's read-only view of every drive."""

    name = models.CharField(max_length=200, unique=True)
    host_path = models.CharField(max_length=1000, unique=True)
    include_patterns = models.TextField(blank=True, default="")
    exclude_patterns = models.TextField(blank=True, default="")
    found = models.BooleanField(default=False)
    """Whether the folder existed at the latest scan."""
    file_count = models.IntegerField(null=True)
    fingerprint = models.CharField(max_length=64, blank=True, default="")
    """Hash of every file's path, size and modified time at the latest scan."""
    scanned_at = models.DateTimeField(null=True)
    scan_error = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def container_path(self) -> Path:
        return container_path(self.host_path, settings.HOST_DRIVES_ROOT)


class VectorDatabase(models.Model):
    name = models.CharField(max_length=200, unique=True)
    engine = models.CharField(max_length=50)
    embedding_model = models.CharField(max_length=100)
    embedder_runtime = models.CharField(max_length=10)
    chunk_min_tokens = models.IntegerField()
    chunk_max_tokens = models.IntegerField()
    chunk_overlap_tokens = models.IntegerField()
    search_mode = models.CharField(max_length=20)
    running = models.BooleanField(default=False)
    built_with = models.JSONField(null=True)
    """The vector settings the stored vectors were made with; null until the engine database exists."""
    created_at = models.DateTimeField(auto_now_add=True)

    def vector_settings(self) -> dict:
        """Settings that change the stored vectors; changing any of them makes old and new vectors incomparable."""
        return {
            "engine": self.engine,
            "embedding_model": self.embedding_model,
            "chunk_min_tokens": self.chunk_min_tokens,
            "chunk_max_tokens": self.chunk_max_tokens,
            "chunk_overlap_tokens": self.chunk_overlap_tokens,
        }

    @property
    def needs_rebuild(self) -> bool:
        return self.built_with is not None and self.built_with != self.vector_settings()


class Assignment(models.Model):
    """A source feeding a database. A disconnected assignment keeps its chunks until the database's next Sync all."""

    database = models.ForeignKey(VectorDatabase, on_delete=models.CASCADE, related_name="assignments")
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name="assignments")
    connected = models.BooleanField(default=True)
    synced_fingerprint = models.CharField(max_length=64, blank=True, default="")
    synced_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["database", "source"], name="one_assignment_per_pair")]


class Job(models.Model):
    class Kind(models.TextChoices):
        CREATE = "create"
        START = "start"
        STOP = "stop"
        SYNC_SOURCE = "sync_source"
        SYNC_ALL = "sync_all"
        DELETE = "delete"
        DOWNLOAD = "download"
        START_GENERATOR = "start_generator"
        STOP_GENERATOR = "stop_generator"
        START_RERANKER = "start_reranker"
        STOP_RERANKER = "stop_reranker"

    class Status(models.TextChoices):
        QUEUED = "queued"
        RUNNING = "running"
        DONE = "done"
        FAILED = "failed"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    title = models.CharField(max_length=300)
    database = models.ForeignKey(VectorDatabase, null=True, on_delete=models.SET_NULL, related_name="jobs")
    source = models.ForeignKey(Source, null=True, on_delete=models.SET_NULL, related_name="jobs")
    PROGRESS_DETAIL_LENGTH = 300

    model_key = models.CharField(max_length=100, blank=True, default="")
    """The model this job downloads: set for download jobs, and for starts whose model was missing."""
    message = models.TextField(blank=True, default="")
    progress_done = models.BigIntegerField(null=True)
    progress_total = models.BigIntegerField(null=True)
    progress_unit = models.CharField(max_length=10, blank=True, default="")
    progress_detail = models.CharField(max_length=PROGRESS_DETAIL_LENGTH, blank=True, default="")
    """Written by studio.jobs.progress while the job runs."""
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True)
    finished_at = models.DateTimeField(null=True)


class InferenceServer(models.Model):
    """The shared generator or reranker container: one row per role, holding the model it runs or last ran."""

    class Role(models.TextChoices):
        GENERATOR = "generator"
        RERANKER = "reranker"

    role = models.CharField(max_length=20, choices=Role.choices, unique=True)
    model_key = models.CharField(max_length=100)
    runtime = models.CharField(max_length=10, default="gpu")
    context = models.IntegerField(default=8192)
    """Generator context window in tokens; unused by the reranker."""
    running = models.BooleanField(default=False)


class LogLine(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10)
    origin = models.CharField(max_length=20)
    message = models.TextField()
