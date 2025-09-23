"""Structured logging configuration."""
import logging
import json
import time
from datetime import datetime
from typing import Dict, Any
import uuid


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "level": record.levelname,
            "ts": datetime.utcnow().isoformat() + "Z",
            "req_id": getattr(record, "req_id", None),
            "route": getattr(record, "route", None),
            "elapsed_ms": getattr(record, "elapsed_ms", None),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging() -> logging.Logger:
    """Set up structured logging."""
    logger = logging.getLogger("pai")
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    return logger


def mask_secrets(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive data in logs."""
    masked_data = data.copy()
    sensitive_keys = ["api_key", "token", "password", "secret", "credentials"]

    for key, value in masked_data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            masked_data[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked_data[key] = mask_secrets(value)

    return masked_data


# Global logger instance
logger = setup_logging()
