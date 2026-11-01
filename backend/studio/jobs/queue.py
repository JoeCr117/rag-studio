"""A one-at-a-time job queue in the metadata database: the API enqueues, the worker runs the oldest queued job."""

import time

from django.db import close_old_connections, transaction
from django.utils import timezone
from loguru import logger

from studio.logs import prune_logs
from studio.models import Job, Source, VectorDatabase

IDLE_SECONDS = 0.5


def enqueue(
    kind: Job.Kind,
    title: str,
    database: VectorDatabase | None = None,
    source: Source | None = None,
    model_key: str = "",
) -> Job:
    job = Job.objects.create(kind=kind, title=title, database=database, source=source, model_key=model_key)
    logger.info("Queued: {}", title)
    return job


def claim_next() -> Job | None:
    with transaction.atomic():
        job = Job.objects.select_for_update(skip_locked=True).filter(status=Job.Status.QUEUED).order_by("id").first()
        if job:
            job.status, job.started_at = Job.Status.RUNNING, timezone.now()
            job.save(update_fields=["status", "started_at"])
        return job


def fail_interrupted() -> None:
    """Jobs left running when the worker stopped (shutdown, rebuild, crash) never finished."""
    count = Job.objects.filter(status=Job.Status.RUNNING).update(
        status=Job.Status.FAILED, message="Interrupted: the worker restarted", finished_at=timezone.now()
    )
    if count:
        logger.warning("{} job(s) were interrupted by a worker restart", count)


def run_forever(handle) -> None:
    fail_interrupted()
    last_prune = 0.0
    while True:
        close_old_connections()
        job = claim_next()
        if job is None:
            if time.monotonic() - last_prune > 60:
                prune_logs()
                last_prune = time.monotonic()
            time.sleep(IDLE_SECONDS)
            continue
        logger.info("Running: {}", job.title)
        try:
            status, message = Job.Status.DONE, handle(job) or ""
            logger.info("Done: {} {}", job.title, message)
        except Exception as error:
            status, message = Job.Status.FAILED, str(error)
            logger.opt(exception=not isinstance(error, JobRefused)).error("Failed: {}: {}", job.title, error)
        # An UPDATE rather than job.save(): a delete job has removed the database the in-memory job still points at.
        Job.objects.filter(pk=job.pk).update(status=status, message=message, finished_at=timezone.now())


class JobRefused(RuntimeError):
    """An expected refusal (for example syncing a stopped database), logged without a traceback."""
