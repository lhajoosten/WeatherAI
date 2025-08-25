"""Centralized logging configuration for WeatherAI.

This module provides structured JSON logging with consistent
formatting and context across all application components.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging(
    level: str = "INFO",
    json_logs: bool = True,
    include_stdlib: bool = True
) -> None:
    """Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_logs: Whether to output JSON format
        include_stdlib: Whether to configure standard library logging
    """

    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
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
            level=getattr(logging, level.upper()),
        )


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
