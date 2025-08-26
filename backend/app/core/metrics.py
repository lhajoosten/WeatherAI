"""Observability metrics for WeatherAI.

This module provides a unified metrics interface with both in-memory storage
for development and Prometheus metrics for production, along with timing
decorators for measuring performance.
"""

from __future__ import annotations

import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any

import structlog

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = structlog.get_logger(__name__)


class PrometheusMetrics:
    """Prometheus metrics collector for production use."""
    
    def __init__(self, registry: CollectorRegistry | None = None):
        """Initialize Prometheus metrics.
        
        Args:
            registry: Optional custom registry, uses default if None
        """
        self.registry = registry or CollectorRegistry()
        self._initialized = False
        self._counters: dict[str, Counter] = {}
        self._histograms: dict[str, Histogram] = {}
        self._gauges: dict[str, Gauge] = {}
        
        # Initialize common metrics
        self._init_common_metrics()
    
    def _init_common_metrics(self) -> None:
        """Initialize commonly used metrics."""
        if self._initialized:
            return
            
        # HTTP metrics
        self._counters["http_requests_total"] = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code"],
            registry=self.registry
        )
        
        self._histograms["http_request_duration_seconds"] = Histogram(
            "http_request_duration_seconds", 
            "HTTP request duration",
            ["method", "endpoint"],
            registry=self.registry
        )
        
        # LLM metrics
        self._counters["llm_requests_total"] = Counter(
            "llm_requests_total",
            "Total LLM requests",
            ["model", "provider"],
            registry=self.registry
        )
        
        self._counters["llm_tokens_total"] = Counter(
            "llm_tokens_total",
            "Total LLM tokens consumed",
            ["model", "type"],  # type: input/output
            registry=self.registry
        )
        
        self._histograms["llm_request_duration_seconds"] = Histogram(
            "llm_request_duration_seconds",
            "LLM request duration",
            ["model", "provider"],
            registry=self.registry
        )
        
        # RAG metrics
        self._counters["rag_queries_total"] = Counter(
            "rag_queries_total",
            "Total RAG queries",
            ["cache_hit"],
            registry=self.registry
        )
        
        self._histograms["rag_retrieval_duration_seconds"] = Histogram(
            "rag_retrieval_duration_seconds",
            "RAG retrieval duration",
            registry=self.registry
        )
        
        self._gauges["rag_documents_retrieved"] = Gauge(
            "rag_documents_retrieved",
            "Number of documents retrieved in last query",
            registry=self.registry
        )
        
        # Cache metrics
        self._counters["cache_operations_total"] = Counter(
            "cache_operations_total",
            "Total cache operations",
            ["operation", "cache_type", "hit"],
            registry=self.registry
        )
        
        self._histograms["cache_operation_duration_seconds"] = Histogram(
            "cache_operation_duration_seconds",
            "Cache operation duration",
            ["operation", "cache_type"],
            registry=self.registry
        )
        
        # Rate limiting metrics
        self._counters["rate_limit_exceeded_total"] = Counter(
            "rate_limit_exceeded_total",
            "Total rate limit violations",
            ["endpoint", "user_type"],
            registry=self.registry
        )
        
        self._initialized = True
    
    def get_counter(self, name: str, labels: list[str] | None = None) -> Counter:
        """Get or create a counter metric."""
        if name not in self._counters:
            self._counters[name] = Counter(
                name, f"Counter metric: {name}", 
                labels or [], registry=self.registry
            )
        return self._counters[name]
    
    def get_histogram(self, name: str, labels: list[str] | None = None) -> Histogram:
        """Get or create a histogram metric."""
        if name not in self._histograms:
            self._histograms[name] = Histogram(
                name, f"Histogram metric: {name}",
                labels or [], registry=self.registry
            )
        return self._histograms[name]
    
    def get_gauge(self, name: str, labels: list[str] | None = None) -> Gauge:
        """Get or create a gauge metric.""" 
        if name not in self._gauges:
            self._gauges[name] = Gauge(
                name, f"Gauge metric: {name}",
                labels or [], registry=self.registry
            )
        return self._gauges[name]
    
    def generate_metrics(self) -> str:
        """Generate Prometheus metrics output."""
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """Get Prometheus content type."""
        return CONTENT_TYPE_LATEST


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


# Global metrics sink and configuration
_metrics_sink = InMemoryMetricsSink()
_prometheus_metrics: PrometheusMetrics | None = None


def get_prometheus_metrics() -> PrometheusMetrics | None:
    """Get the global Prometheus metrics instance."""
    return _prometheus_metrics


def initialize_prometheus_metrics(registry: CollectorRegistry | None = None) -> PrometheusMetrics:
    """Initialize Prometheus metrics if available."""
    global _prometheus_metrics
    
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, using in-memory metrics only")
        return None
    
    if _prometheus_metrics is None:
        _prometheus_metrics = PrometheusMetrics(registry)
        logger.info("Prometheus metrics initialized")
    
    return _prometheus_metrics


def is_prometheus_enabled() -> bool:
    """Check if Prometheus metrics are enabled."""
    return os.getenv("ENABLE_PROMETHEUS_METRICS", "true").lower() in ("true", "1", "yes")


def record_metric(name: str, value: float, tags: dict[str, str] | None = None) -> None:
    """Record a metric with both in-memory and Prometheus sinks.

    Args:
        name: Metric name (e.g., 'llm.tokens.consumed', 'rag.query.duration')
        value: Metric value
        tags: Optional tags for categorization
    """
    # Always record to in-memory sink
    _metrics_sink.record(name, value, tags)
    
    # Record to Prometheus if available and enabled
    if _prometheus_metrics and is_prometheus_enabled():
        try:
            # Convert dots to underscores for Prometheus compatibility
            prom_name = name.replace(".", "_")
            
            # Determine metric type and record appropriately
            if name.endswith((".duration", ".duration_seconds", ".latency_ms")):
                # Duration metrics go to histograms
                labels = list(tags.keys()) if tags else []
                label_values = list(tags.values()) if tags else []
                
                hist = _prometheus_metrics.get_histogram(prom_name, labels)
                if label_values:
                    hist.labels(*label_values).observe(value)
                else:
                    hist.observe(value)
            
            elif name.endswith((".count", ".total")) or value == 1:
                # Counter metrics
                labels = list(tags.keys()) if tags else []
                label_values = list(tags.values()) if tags else []
                
                counter = _prometheus_metrics.get_counter(prom_name, labels)
                if label_values:
                    counter.labels(*label_values).inc(value)
                else:
                    counter.inc(value)
            
            else:
                # Gauge metrics for everything else
                labels = list(tags.keys()) if tags else []
                label_values = list(tags.values()) if tags else []
                
                gauge = _prometheus_metrics.get_gauge(prom_name, labels)
                if label_values:
                    gauge.labels(*label_values).set(value)
                else:
                    gauge.set(value)
                    
        except Exception as e:
            logger.warning("Failed to record Prometheus metric", error=str(e), metric_name=name)


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
