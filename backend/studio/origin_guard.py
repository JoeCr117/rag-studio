"""Refuses requests that change state when a browser says they come from another site (cross-site request forgery).

CORS only stops a foreign page from reading responses; a body-less POST such as /api/shutdown is still sent. Browsers
always name the page's origin on such requests, so anything not from the UI is refused. Requests without an Origin
header (curl, scripts on this machine) pass.
"""

from collections.abc import Callable, Collection

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}


def is_foreign_write(method: str, origin: str | None, allowed_origins: Collection[str]) -> bool:
    return method not in READ_ONLY_METHODS and origin is not None and origin not in allowed_origins


class OriginGuardMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        origin = request.headers.get("Origin")
        if is_foreign_write(request.method, origin, settings.CORS_ALLOWED_ORIGINS):
            return JsonResponse({"detail": f"Refused: request from {origin}, not from RAG Studio's page"}, status=403)
        return self.get_response(request)
