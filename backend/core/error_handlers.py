"""Unified error handlers mapping exceptions to the standardized API error shape."""

import logging

from django.http import HttpRequest, JsonResponse
from ninja.errors import ValidationError as NinjaValidationError
from pydantic import ValidationError as PydanticValidationError

from core.errors import AppError
from core.logging import current_request_id

logger = logging.getLogger("core.errors")


def format_error_response(
    code: str,
    message: str,
    status_code: int,
    request: HttpRequest | None = None,
) -> JsonResponse:
    """Format and return a standardized JSON error response."""
    req_id = ""
    if request and hasattr(request, "request_id"):
        req_id = request.request_id
    elif current_request_id.get():
        req_id = current_request_id.get()

    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": req_id,
        }
    }
    response = JsonResponse(payload, status=status_code)
    if req_id:
        response["X-Request-ID"] = req_id
    return response


def handle_app_error(request: HttpRequest, exc: AppError) -> JsonResponse:
    """Handler for known application domain and infrastructure errors."""
    return format_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        request=request,
    )


def handle_validation_error(
    request: HttpRequest,
    exc: NinjaValidationError | PydanticValidationError,
) -> JsonResponse:
    """Handler for Ninja and Pydantic validation errors."""
    error_details = []
    raw_errors = getattr(exc, "errors", None)
    if callable(raw_errors):
        err_list = raw_errors()
    elif isinstance(raw_errors, list):
        err_list = raw_errors
    else:
        err_list = []

    for err in err_list:
        if isinstance(err, dict):
            loc = ".".join(str(p) for p in err.get("loc", []))
            msg = err.get("msg", "Invalid value")
            error_details.append(f"{loc}: {msg}" if loc else msg)
        else:
            error_details.append(str(err))

    message = "; ".join(error_details) if error_details else "Invalid query parameters."

    return format_error_response(
        code="VALIDATION_FAILED",
        message=message,
        status_code=422,
        request=request,
    )


def handle_unexpected_error(request: HttpRequest, exc: Exception) -> JsonResponse:
    """Catch-all handler: logs unexpected error once with traceback and returns safe generic 500."""
    req_id = getattr(request, "request_id", "") or current_request_id.get()
    logger.exception("Unexpected server error [request_id=%s]: %s", req_id, str(exc))

    return format_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred. Please try again later.",
        status_code=500,
        request=request,
    )
