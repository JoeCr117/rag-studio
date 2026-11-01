import time

from django.conf import settings
from django.core.management.base import BaseCommand
from loguru import logger

from studio import control_client
from studio.inference.servers import mark_missing_containers_stopped
from studio.jobs.handlers import handle
from studio.jobs.queue import run_forever
from studio.logs import configure_logging
from studio.model_downloads import remove_partial_downloads
from studio.sources.scanner import start_scanner_thread


def running_container_names(attempts: int = 10) -> set[str] | None:
    """Retries while the control sidecar, started alongside the worker, begins listening."""
    for attempt in range(attempts):
        try:
            return {container["name"] for container in control_client.containers() if container["state"] == "running"}
        except control_client.ControlError as error:
            if attempt == attempts - 1:
                logger.warning("Could not compare running flags with containers: {}", error)
            time.sleep(1)
    return None


def reconcile_running_flags() -> None:
    """After a crash or a `docker compose down` outside the UI, databases and servers may still be marked running."""
    running = running_container_names()
    if running is None:
        return
    stale = mark_missing_containers_stopped(running)
    if stale:
        logger.info("Marked stopped (their containers are gone): {}", ", ".join(stale))


def clean_up_interrupted_downloads() -> None:
    freed = remove_partial_downloads(settings.MODELS_DIR)
    if freed:
        logger.info("Removed partial downloads left by an interrupted download ({:.2f} GB freed)", freed / 1e9)


class Command(BaseCommand):
    help = "Scan sources every second and run queued jobs one at a time."

    def handle(self, *args, **options) -> None:
        configure_logging("worker")
        logger.info("Worker started")
        reconcile_running_flags()
        clean_up_interrupted_downloads()
        start_scanner_thread()
        run_forever(handle)
