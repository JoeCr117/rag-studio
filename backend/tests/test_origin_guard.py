import pytest
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from studio.origin_guard import OriginGuardMiddleware, is_foreign_write

UI = "http://localhost:3000"


@pytest.mark.parametrize(
    ("method", "origin", "refused"),
    [
        ("POST", "https://evil.example", True),
        ("DELETE", "null", True),
        ("POST", UI, False),
        ("POST", None, False),
        ("GET", "https://evil.example", False),
        ("OPTIONS", "https://evil.example", False),
    ],
)
def test_only_writes_from_a_foreign_page_are_refused(method, origin, refused):
    assert is_foreign_write(method, origin, [UI]) is refused


@override_settings(CORS_ALLOWED_ORIGINS=[UI])
def test_the_middleware_answers_403_without_running_the_view():
    calls = []
    guard = OriginGuardMiddleware(lambda request: calls.append(request) or HttpResponse("ran"))
    refused = guard(RequestFactory().post("/api/shutdown", headers={"Origin": "https://evil.example"}))
    allowed = guard(RequestFactory().post("/api/shutdown", headers={"Origin": UI}))
    assert refused.status_code == 403
    assert allowed.content == b"ran"
    assert len(calls) == 1
