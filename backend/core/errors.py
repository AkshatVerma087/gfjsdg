"""Application error taxonomy."""


class AppError(Exception):
    """Base application exception for domain and infrastructure errors."""

    default_code = "INTERNAL_ERROR"
    default_status_code = 500
    default_message = "An unexpected error occurred."

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        status_code: int | None = None,
    ):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status_code
        super().__init__(self.message)


class ValidationFailed(AppError):
    """Raised when client input fails parameter or schema validation."""

    default_code = "VALIDATION_FAILED"
    default_status_code = 422
    default_message = "Input validation failed."


class NotFound(AppError):
    """Raised when requested resource or date is outside the ingested window."""

    default_code = "NOT_FOUND"
    default_status_code = 404
    default_message = "The requested resource was not found."


class UpstreamUnavailable(AppError):
    """Raised when an external dependency (such as Elexon API) is unreachable."""

    default_code = "UPSTREAM_UNAVAILABLE"
    default_status_code = 503
    default_message = "Upstream service is currently unavailable."
