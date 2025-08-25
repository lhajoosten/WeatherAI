"""Observability metrics for WeatherAI.

This module provides a simple metrics interface with in-memory storage
and a timing decorator for measuring performance.
"""

from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MetricRecord:
    """A single metric measurement."""
    name: str
    value: float
    tags: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class InMemoryMetricsSink:
    """Simple in-memory metrics storage for development and testing."""

    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self._metrics: list[MetricRecord] = []

    def record(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """Record a metric measurement."""
        metric = MetricRecord(name=name, value=value, tags=tags or {})
        self._metrics.append(metric)

        # Keep only the most recent records
        if len(self._metrics) > self.max_records:
            self._metrics = self._metrics[-self.max_records:]

        logger.debug("Metric recorded", name=name, value=value, tags=tags)

    def get_metrics(self, name: str | None = None) -> list[MetricRecord]:
        """Get recorded metrics, optionally filtered by name."""
        if name:
            return [m for m in self._metrics if m.name == name]
        return self._metrics.copy()

    def clear(self) -> None:
        """Clear all recorded metrics."""
        self._metrics.clear()

    def get_summary(self) -> dict[str, int]:
        """Get a summary of metric counts by name."""
        summary = {}
        for metric in self._metrics:
            summary[metric.name] = summary.get(metric.name, 0) + 1
        return summary


# Global metrics sink
_metrics_sink = InMemoryMetricsSink()


def record_metric(name: str, value: float, tags: dict[str, str] | None = None) -> None:
    """Record a metric with the global sink.

    Args:
        name: Metric name (e.g., 'llm.tokens.consumed', 'rag.query.duration')
        value: Metric value
        tags: Optional tags for categorization
    """
    _metrics_sink.record(name, value, tags)


def get_metrics_sink() -> InMemoryMetricsSink:
    """Get the global metrics sink for testing and inspection."""
    return _metrics_sink


@contextmanager
def measure_time(metric_name: str, tags: dict[str, str] | None = None) -> Generator[None, None, None]:
    """Context manager for measuring execution time.

    Args:
        metric_name: Name of the timing metric
        tags: Optional tags for categorization
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        record_metric(f"{metric_name}.duration_seconds", duration, tags)


def timing(metric_name: str | None = None, tags: dict[str, str] | None = None):
    """Decorator for measuring function execution time.

    Args:
        metric_name: Optional metric name (defaults to function name)
        tags: Optional tags for categorization
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            with measure_time(name, tags):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            with measure_time(name, tags):
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Common metrics helpers
def record_llm_usage(
    model: str,
    tokens_in: int,
    tokens_out: int,
    duration_seconds: float
) -> None:
    """Record LLM usage metrics."""
    tags = {"model": model}
    record_metric("llm.tokens.input", tokens_in, tags)
    record_metric("llm.tokens.output", tokens_out, tags)
    record_metric("llm.tokens.total", tokens_in + tokens_out, tags)
    record_metric("llm.request.duration_seconds", duration_seconds, tags)


def record_rag_query(
    query_length: int,
    retrieved_docs: int,
    response_length: int,
    duration_seconds: float
) -> None:
    """Record RAG query metrics."""
    record_metric("rag.query.length", query_length)
    record_metric("rag.documents.retrieved", retrieved_docs)
    record_metric("rag.response.length", response_length)
    record_metric("rag.query.duration_seconds", duration_seconds)


def record_cache_operation(operation: str, hit: bool, duration_seconds: float) -> None:
    """Record cache operation metrics."""
    tags = {"operation": operation, "hit": str(hit)}
    record_metric("cache.operation", 1, tags)
    record_metric("cache.operation.duration_seconds", duration_seconds, tags)
