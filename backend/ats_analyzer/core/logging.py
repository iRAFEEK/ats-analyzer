"""Structured logging configuration."""

import logging
import sys
from typing import Any

import structlog
from structlog.typing import FilteringBoundLogger

from ats_analyzer.core.config import get_settings


def setup_logging() -> None:
    """Configure structured logging."""
    settings = get_settings()
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer() if settings.LOG_LEVEL == "DEBUG" 
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, settings.LOG_LEVEL.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )


def get_logger(name: str = "") -> FilteringBoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


def redact_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive information from logs."""
    sensitive_keys = {"text", "content", "resume_text", "jd_text"}
    
    redacted = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys:
            if isinstance(value, str):
                redacted[key] = f"<redacted:{len(value)} chars>"
            else:
                redacted[key] = "<redacted>"
        else:
            redacted[key] = value
    
    return redacted
