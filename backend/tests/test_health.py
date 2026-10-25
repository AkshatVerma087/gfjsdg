"""Tests for health and readiness endpoints (P2-T04)."""

import json
from unittest.mock import patch

from django.db import DatabaseError
from django.test import Client


def test_health_probe_returns_200(client: Client):
    """Liveness probe /api/v1/health returns 200 with ok status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = json.loads(response.content.decode("utf-8"))
    assert data["status"] == "ok"
    assert data["app"] == "wind-forecast-monitor"


def test_ready_probe_returns_200_when_database_accessible(client: Client):
    """Readiness probe /api/v1/ready returns 200 when database is healthy."""
    with patch("django.db.connection.ensure_connection", return_value=None):
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        data = json.loads(response.content.decode("utf-8"))
        assert data["status"] == "ready"
        assert data["database"] == "connected"


def test_ready_probe_returns_503_when_database_unreachable(client: Client):
    """Readiness probe returns 503 without leaking connection credentials when DB fails."""
    with patch(
        "django.db.connection.ensure_connection",
        side_effect=DatabaseError("Connection timeout to 10.0.0.1"),
    ):
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        content = response.content.decode("utf-8")
        data = json.loads(content)
        assert data["status"] == "unhealthy"
        assert data["database"] == "unavailable"
        assert "10.0.0.1" not in content
