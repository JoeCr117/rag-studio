"""Background loop that rescans every registered source once a second and records what changed."""

import threading
import time

from django.db import close_old_connections
from django.utils import timezone
from loguru import logger

from studio.models import Source
from studio.sources.scanning import ScannedFile, file_changes, pattern_lines, scan_source

SCAN_INTERVAL_SECONDS = 1.0


class SourceScanner:
    def __init__(self) -> None:
        self._previous: dict[int, tuple[ScannedFile, ...]] = {}

    def scan_all(self) -> None:
        for source in Source.objects.all():
            self._scan(source)

    def _scan(self, source: Source) -> None:
        if not source.container_path.is_dir():
            if source.found:
                logger.warning("Source '{}': folder not found at {}", source.name, source.host_path)
                Source.objects.filter(pk=source.pk).update(found=False)
            return
        try:
            result = scan_source(
                source.container_path, pattern_lines(source.include_patterns), pattern_lines(source.exclude_patterns)
            )
        except OSError as error:
            Source.objects.filter(pk=source.pk).update(found=True, scan_error=str(error), scanned_at=timezone.now())
            return
        previous = self._previous.get(source.pk)
        self._previous[source.pk] = result.files
        if result.fingerprint == source.fingerprint and source.found and not source.scan_error:
            return
        if previous is not None or source.fingerprint:
            changes = file_changes(previous or (), result.files) if previous is not None else None
            summary = (
                f"+{changes.added} -{changes.removed} ~{changes.modified}" if changes else "changed since last run"
            )
            logger.info("Source '{}': {} ({} files)", source.name, summary, len(result.files))
        else:
            logger.info("Source '{}' found: {} files", source.name, len(result.files))
        Source.objects.filter(pk=source.pk).update(
            found=True,
            fingerprint=result.fingerprint,
            file_count=len(result.files),
            scan_error="",
            scanned_at=timezone.now(),
        )


def run_scanner_forever() -> None:
    scanner = SourceScanner()
    while True:
        try:
            close_old_connections()
            scanner.scan_all()
        except Exception:
            logger.exception("Source scan failed")
        time.sleep(SCAN_INTERVAL_SECONDS)


def start_scanner_thread() -> threading.Thread:
    thread = threading.Thread(target=run_scanner_forever, name="source-scanner", daemon=True)
    thread.start()
    return thread
