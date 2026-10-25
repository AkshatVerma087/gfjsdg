"""Tests for error taxonomy and API error format (P2-T03)."""

import json

from django.test import RequestFactory

from core.error_handlers import handle_app_error, handle_unexpected_error
from core.errors import NotFound, UpstreamUnavailable, ValidationFailed


def test_validation_failed_maps_to_422():
    """ValidationFailed exception maps to HTTP 422 with standardized shape."""
    factory = RequestFactory()
    request = factory.get("/api/v1/forecast")
    request.request_id = "req-val-1"

    exc = ValidationFailed("Delivery date is required.")
    response = handle_app_error(request, exc)

    assert response.status_code == 422
    data = json.loads(response.content.decode("utf-8"))
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_FAILED"
    assert data["error"]["message"] == "Delivery date is required."
    assert data["error"]["request_id"] == "req-val-1"
    assert response["X-Request-ID"] == "req-val-1"


def test_not_found_maps_to_404():
    """NotFound exception maps to HTTP 404."""
    factory = RequestFactory()
    request = factory.get("/api/v1/forecast")
    request.request_id = "req-404-1"

    exc = NotFound("Date 2026-03-01 is outside ingested window.")
    response = handle_app_error(request, exc)

    assert response.status_code == 404
    data = json.loads(response.content.decode("utf-8"))
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Date 2026-03-01 is outside ingested window."
    assert data["error"]["request_id"] == "req-404-1"


def test_upstream_unavailable_maps_to_503():
    """UpstreamUnavailable exception maps to HTTP 503."""
    factory = RequestFactory()
    request = factory.get("/api/v1/forecast")
    request.request_id = "req-503-1"

    exc = UpstreamUnavailable("Elexon BMRS endpoint timed out.")
    response = handle_app_error(request, exc)

    assert response.status_code == 503
    data = json.loads(response.content.decode("utf-8"))
    assert data["error"]["code"] == "UPSTREAM_UNAVAILABLE"
    assert data["error"]["message"] == "Elexon BMRS endpoint timed out."


def test_unexpected_exception_maps_to_500_without_leaking_internals():
    """Unexpected exception must return a safe generic message without tracebacks."""
    factory = RequestFactory()
    request = factory.get("/api/v1/forecast")
    request.request_id = "req-500-1"

    raw_exc = RuntimeError(
        "Database connection string: postgresql://admin:secret_pass@db.internal:5432"
    )
    response = handle_unexpected_error(request, raw_exc)

    assert response.status_code == 500
    content = response.content.decode("utf-8")
    data = json.loads(content)

    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert "secret_pass" not in content
    assert "postgresql://" not in content
    assert "Traceback" not in content
    assert data["error"]["message"] == "An unexpected error occurred. Please try again later."
    assert data["error"]["request_id"] == "req-500-1"
