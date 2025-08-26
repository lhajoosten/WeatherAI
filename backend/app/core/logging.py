"""Centralized logging configuration for WeatherAI.

This module provides structured JSON logging with consistent
formatting and context across all application components.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from contextvars import ContextVar
from typing import Any

import structlog

# Context variables for correlation tracking
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)


def add_correlation_context(logger, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add correlation IDs and service context to log events."""
    # Add service information
    event_dict["service"] = os.getenv("SERVICE_NAME", "weatherai-backend")
    event_dict["environment"] = os.getenv("ENVIRONMENT", "development")
    
    # Add correlation IDs if available
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict["trace_id"] = trace_id
    
    user_id = user_id_var.get()
    if user_id:
        event_dict["user_id"] = user_id
    
    return event_dict


def configure_logging(
    level: str = "INFO",
    json_logs: bool = True,
    include_stdlib: bool = True,
    service_name: str | None = None
) -> None:
    """Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR) - can be overridden by LOG_LEVEL env var
        json_logs: Whether to output JSON format - can be overridden by JSON_LOGS env var
        include_stdlib: Whether to configure standard library logging
        service_name: Service name for logging context - can be overridden by SERVICE_NAME env var
    """
    # Allow environment overrides
    level = os.getenv("LOG_LEVEL", level).upper()
    json_logs = os.getenv("JSON_LOGS", str(json_logs)).lower() in ("true", "1", "yes")
    
    # Set service name from environment if not provided
    if service_name:
        os.environ.setdefault("SERVICE_NAME", service_name)

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        add_correlation_context,  # Add our correlation processor
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    if include_stdlib:
        # Configure standard library logging
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, level),
        )


def set_correlation_id(request_id: str | None = None, trace_id: str | None = None, user_id: str | None = None) -> None:
    """Set correlation IDs for the current context.
    
    Args:
        request_id: Unique request identifier
        trace_id: Distributed trace identifier  
        user_id: User identifier (optional)
    """
    if request_id:
        request_id_var.set(request_id)
    if trace_id:
        trace_id_var.set(trace_id)
    if user_id:
        user_id_var.set(user_id)


def generate_request_id() -> str:
    """Generate a new request ID."""
    return str(uuid.uuid4())


def get_correlation_context() -> dict[str, str | None]:
    """Get current correlation context."""
    return {
        "request_id": request_id_var.get(),
        "trace_id": trace_id_var.get(),
        "user_id": user_id_var.get(),
    }


def get_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with optional context.

    Args:
        name: Logger name (usually __name__)
        **context: Additional context to bind to the logger

    Returns:
        Bound logger instance with context
    """
    logger = structlog.get_logger(name)
    if context:
        logger = logger.bind(**context)
    return logger


def get_tagged_logger(tag: str, name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger with a specific tag for categorization.

    Args:
        tag: Tag to categorize logs (e.g., 'API', 'DB', 'RAG', 'LLM')
        name: Logger name (usually __name__)
        **context: Additional context to bind to the logger

    Returns:
        Bound logger instance with tag and context
    """
    logger = structlog.get_logger(name)
    logger = logger.bind(tag=tag)
    if context:
        logger = logger.bind(**context)
    return logger


# Pre-configured loggers for common categories
def get_api_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger tagged for API operations."""
    return get_tagged_logger("API", name, **context)


def get_db_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger tagged for database operations."""
    return get_tagged_logger("DB", name, **context)


def get_rag_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger tagged for RAG operations."""
    return get_tagged_logger("RAG", name, **context)


def get_llm_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger tagged for LLM operations."""
    return get_tagged_logger("LLM", name, **context)


def get_cache_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger tagged for cache operations."""
    return get_tagged_logger("CACHE", name, **context)


def get_analytics_logger(name: str, **context: Any) -> structlog.stdlib.BoundLogger:
    """Get a logger tagged for analytics operations."""
    return get_tagged_logger("ANALYTICS", name, **context)
