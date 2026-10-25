"""Core HTTP middlewares."""

import logging
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from core.logging import current_request_id

access_logger = logging.getLogger("core.access")


class RequestIDMiddleware:
    """Assigns or propagates an X-Request-ID header and logs an access line per request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming_id = request.headers.get("X-Request-ID", "").strip()
        request_id = incoming_id if incoming_id else str(uuid.uuid4())
        request.request_id = request_id

        # Bind to contextvar so any downstream log statement picks it up
        token = current_request_id.set(request_id)
        start_time = time.perf_counter()

        try:
            response = self.get_response(request)
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = getattr(response, "status_code", 500) if "response" in locals() else 500

            access_logger.info(
                "%s %s %s (%.2f ms)",
                request.method,
                request.path,
                status_code,
                duration_ms,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )
            current_request_id.reset(token)

        response["X-Request-ID"] = request_id
        return response
