"""Loguru writes every log line to stderr and to the LogLine table, which the UI's terminal panel streams."""

import sys
from contextlib import suppress

from django.db import DatabaseError
from loguru import logger

KEEP_LINES = 5000


def _database_sink(origin: str):
    def write(message) -> None:
        from studio.models import LogLine

        record = message.record
        with suppress(DatabaseError):  # a database still starting must not stop logging to stderr
            LogLine.objects.create(level=record["level"].name, origin=origin, message=record["message"])

    return write


def configure_logging(origin: str) -> None:
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    logger.add(_database_sink(origin), level="INFO", format="{message}")


def prune_logs() -> None:
    from studio.models import LogLine

    cutoff = LogLine.objects.order_by("-id").values_list("id", flat=True)[KEEP_LINES : KEEP_LINES + 1].first()
    if cutoff:
        LogLine.objects.filter(id__lte=cutoff).delete()
