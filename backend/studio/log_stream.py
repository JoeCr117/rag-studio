"""Server-Sent Events: the terminal panel keeps one HTTP response open and receives each new log line as an event."""

import json
import time

from django.db import close_old_connections
from django.http import StreamingHttpResponse

from studio.models import LogLine

BACKLOG = 300
POLL_SECONDS = 0.5
KEEPALIVE_SECONDS = 15


def _event(line: LogLine) -> str:
    payload = {"at": line.created_at.isoformat(), "level": line.level, "origin": line.origin, "message": line.message}
    return f"id: {line.id}\ndata: {json.dumps(payload)}\n\n"


def _lines_after(last_id: int):
    if last_id == 0:
        backlog = list(LogLine.objects.order_by("-id")[:BACKLOG])
        yield from (_event(line) for line in reversed(backlog))
        last_id = backlog[0].id if backlog else 0
    quiet_since = time.monotonic()
    while True:
        lines = list(LogLine.objects.filter(id__gt=last_id).order_by("id")[:200])
        close_old_connections()
        for line in lines:
            last_id = line.id
            yield _event(line)
        if lines:
            quiet_since = time.monotonic()
        elif time.monotonic() - quiet_since > KEEPALIVE_SECONDS:
            yield ": keepalive\n\n"
            quiet_since = time.monotonic()
        time.sleep(POLL_SECONDS)


def stream_logs(request):
    last_id = int(request.headers.get("Last-Event-ID") or request.GET.get("after") or 0)
    response = StreamingHttpResponse(_lines_after(last_id), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
