"""Structured logging and secret redaction filters."""

import contextvars
import json
import logging
import re
from datetime import UTC, datetime

# Context variable holding the active request ID for the current thread/task
current_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_request_id", default=""
)

REDACTED_PATTERNS = [
    re.compile(r"(secret|password|token|authorization|bearer|key|credential)", re.IGNORECASE)
]


class RequestIDFilter(logging.Filter):
    """Injects current_request_id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = (
            current_request_id.get() or getattr(record, "request_id", "") or "system"
        )
        return True


class SecretRedactionFilter(logging.Filter):
    """Masks secret-like keys or patterns in log messages and attributes."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact_string(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.redact_value(k, v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self.redact_string(str(a)) if isinstance(a, str) else a for a in record.args
                )
        return True

    @classmethod
    def redact_value(cls, key: str, value: object) -> object:
        if any(pat.search(key) for pat in REDACTED_PATTERNS):
            return "[REDACTED]"
        if isinstance(value, str):
            return cls.redact_string(value)
        return value

    @classmethod
    def redact_string(cls, text: str) -> str:
        # Match key=value or key: value
        redacted = re.sub(
            r"(?i)(secret|password|token|bearer|key|authorization)([:=\s]+)([^\s,;]+)",
            r"\1\2[REDACTED]",
            text,
        )
        return redacted


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include custom extra fields if present
        for key in ("method", "path", "status_code", "duration_ms"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry)
