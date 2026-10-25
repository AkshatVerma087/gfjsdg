"""Health and readiness endpoints for Docker and uptime probes."""

from django.db import connection
from django.http import HttpRequest, JsonResponse


def health_view(request: HttpRequest) -> JsonResponse:
    """Liveness probe: verifies the process is running."""
    return JsonResponse({"status": "ok", "app": "wind-forecast-monitor"})


def ready_view(request: HttpRequest) -> JsonResponse:
    """Readiness probe: verifies the database connection is functional."""
    try:
        connection.ensure_connection()
        return JsonResponse({"status": "ready", "database": "connected"})
    except Exception:
        return JsonResponse({"status": "unhealthy", "database": "unavailable"}, status=503)
