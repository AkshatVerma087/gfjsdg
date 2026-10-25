"""Tests for structured logging and request IDs (P2-T02)."""

import json
import logging

from django.http import HttpResponse
from django.test import Client, RequestFactory

from core.logging import JSONFormatter, SecretRedactionFilter, current_request_id
from core.middleware import RequestIDMiddleware


def test_request_id_middleware_assigns_and_propagates_header():
    """Middleware must generate an X-Request-ID header if none provided."""
    factory = RequestFactory()
    request = factory.get("/api/v1/health")

    def dummy_view(req):
        assert hasattr(req, "request_id")
        assert len(req.request_id) > 0
        return HttpResponse("OK")

    middleware = RequestIDMiddleware(dummy_view)
    response = middleware(request)

    assert "X-Request-ID" in response
    assert response["X-Request-ID"] == request.request_id


def test_request_id_middleware_respects_incoming_header():
    """Middleware must preserve incoming X-Request-ID header."""
    factory = RequestFactory()
    custom_id = "test-custom-request-id-12345"
    request = factory.get("/api/v1/health", HTTP_X_REQUEST_ID=custom_id)

    def dummy_view(req):
        assert req.request_id == custom_id
        return HttpResponse("OK")

    middleware = RequestIDMiddleware(dummy_view)
    response = middleware(request)

    assert response["X-Request-ID"] == custom_id


def test_secret_redaction_filter():
    """Secret patterns must be masked in log messages and record dictionaries."""
    redaction_filter = SecretRedactionFilter()

    # Test string redaction
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Connecting with password=secret_value_123 and token: my_secret_token",
        args=(),
        exc_info=None,
    )
    redaction_filter.filter(record)
    assert "secret_value_123" not in record.msg
    assert "my_secret_token" not in record.msg
    assert "password=[REDACTED]" in record.msg
    assert "token: [REDACTED]" in record.msg

    # Test dictionary args redaction
    dict_record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Config payload",
        args={"api_key": "raw_secret_api_key", "username": "public_user"},
        exc_info=None,
    )
    redaction_filter.filter(dict_record)
    assert dict_record.args["api_key"] == "[REDACTED]"
    assert dict_record.args["username"] == "public_user"


def test_json_formatter_includes_request_id():
    """JSONFormatter should output valid JSON with request_id and metadata."""
    formatter = JSONFormatter()
    token = current_request_id.set("req-test-999")
    try:
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Processing analytical calculation",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-test-999"
        record.duration_ms = 45.2
        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["request_id"] == "req-test-999"
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Processing analytical calculation"
        assert parsed["duration_ms"] == 45.2
        assert "timestamp" in parsed
    finally:
        current_request_id.reset(token)


def test_health_endpoint_returns_request_id_header(client: Client):
    """Client call to /api/v1/health returns X-Request-ID."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response
    assert len(response["X-Request-ID"]) > 0
