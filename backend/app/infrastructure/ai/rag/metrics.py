"""Metrics and observability for RAG pipeline."""

from typing import Dict, Any, List
import time
import structlog
from contextlib import asynccontextmanager

logger = structlog.get_logger(__name__)


class RAGMetrics:
    """
    Metrics collection for RAG pipeline.
    
    This is a basic implementation that logs metrics.
    TODO: Integrate with proper metrics collection system (Prometheus, etc.)
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._counters = {}
        self._histograms = {}
        self._gauges = {}
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        labels = labels or {}
        key = f"{name}_{self._labels_to_key(labels)}"
        self._counters[key] = self._counters.get(key, 0) + value
        
        logger.debug(
            "Counter incremented",
            metric=name,
            value=value,
            labels=labels,
            total=self._counters[key]
        )
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value."""
        labels = labels or {}
        key = f"{name}_{self._labels_to_key(labels)}"
        
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        
        logger.debug(
            "Histogram recorded",
            metric=name,
            value=value,
            labels=labels
        )
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value."""
        labels = labels or {}
        key = f"{name}_{self._labels_to_key(labels)}"
        self._gauges[key] = value
        
        logger.debug(
            "Gauge set",
            metric=name,
            value=value,
            labels=labels
        )
    
    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """Convert labels dict to string key."""
        if not labels:
            return ""
        return "_".join(f"{k}={v}" for k, v in sorted(labels.items()))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics."""
        histogram_stats = {}
        for key, values in self._histograms.items():
            if values:
                histogram_stats[key] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values)
                }
        
        return {
            "counters": dict(self._counters),
            "histograms": histogram_stats,
            "gauges": dict(self._gauges)
        }


# Global metrics instance
_metrics = RAGMetrics()


def get_metrics() -> RAGMetrics:
    """Get global metrics instance."""
    return _metrics


# Metric helper functions
def record_retrieval_latency(latency_ms: float, status: str = "success"):
    """Record retrieval latency metric."""
    _metrics.record_histogram(
        "weatherai_rag_retrieval_latency_ms",
        latency_ms,
        {"status": status}
    )


def record_chunk_count(count: int, stage: str):
    """Record chunk count at different pipeline stages."""
    _metrics.set_gauge(
        "weatherai_rag_chunk_count",
        count,
        {"stage": stage}
    )


def record_context_tokens(token_count: int):
    """Record context token usage."""
    _metrics.record_histogram(
        "weatherai_rag_context_tokens",
        token_count
    )


def record_cache_hit(cache_type: str, hit: bool):
    """Record cache hit/miss."""
    _metrics.increment_counter(
        "weatherai_rag_cache_hit",
        1,
        {"cache_type": cache_type, "hit": str(hit).lower()}
    )


def record_similarity_min(similarity: float):
    """Record minimum similarity score in results."""
    _metrics.set_gauge(
        "weatherai_rag_similarity_min",
        similarity
    )


def record_generation_latency(latency_ms: float, model: str = "unknown"):
    """Record LLM generation latency."""
    _metrics.record_histogram(
        "weatherai_rag_generation_latency_ms",
        latency_ms,
        {"model": model}
    )


def record_pipeline_error(error_type: str, stage: str):
    """Record pipeline errors."""
    _metrics.increment_counter(
        "weatherai_rag_pipeline_errors",
        1,
        {"error_type": error_type, "stage": stage}
    )


# Context managers for automatic timing
@asynccontextmanager
async def time_retrieval():
    """Context manager to time retrieval operations."""
    start_time = time.time()
    status = "success"
    try:
        yield
    except Exception:
        status = "error"
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000
        record_retrieval_latency(latency_ms, status)


@asynccontextmanager
async def time_generation(model: str = "unknown"):
    """Context manager to time generation operations."""
    start_time = time.time()
    try:
        yield
    finally:
        latency_ms = (time.time() - start_time) * 1000
        record_generation_latency(latency_ms, model)


# Metrics reporting
def log_pipeline_metrics(
    query: str,
    num_retrieved: int,
    num_filtered: int,
    min_similarity: float,
    context_tokens: int,
    cache_hits: Dict[str, bool] = None
):
    """Log comprehensive pipeline metrics for a query."""
    cache_hits = cache_hits or {}
    
    # Record all metrics
    record_chunk_count(num_retrieved, "retrieved")
    record_chunk_count(num_filtered, "filtered")
    record_similarity_min(min_similarity)
    record_context_tokens(context_tokens)
    
    for cache_type, hit in cache_hits.items():
        record_cache_hit(cache_type, hit)
    
    # Log summary
    logger.info(
        "RAG pipeline metrics",
        query_length=len(query),
        chunks_retrieved=num_retrieved,
        chunks_filtered=num_filtered,
        min_similarity=min_similarity,
        context_tokens=context_tokens,
        cache_hits=cache_hits
    )


def reset_metrics():
    """Reset all metrics (useful for testing)."""
    global _metrics
    _metrics = RAGMetrics()


# Health check metrics
def get_pipeline_health() -> Dict[str, Any]:
    """Get pipeline health metrics."""
    stats = _metrics.get_stats()
    
    # Calculate health indicators
    total_queries = sum(
        count for key, count in stats["counters"].items()
        if "weatherai_rag_retrieval_latency_ms" in key
    )
    
    error_rate = 0.0
    if total_queries > 0:
        total_errors = sum(
            count for key, count in stats["counters"].items()
            if "weatherai_rag_pipeline_errors" in key
        )
        error_rate = total_errors / total_queries
    
    # Average latencies
    avg_retrieval_latency = 0.0
    avg_generation_latency = 0.0
    
    retrieval_stats = stats["histograms"].get("weatherai_rag_retrieval_latency_ms_", {})
    generation_stats = stats["histograms"].get("weatherai_rag_generation_latency_ms_", {})
    
    if retrieval_stats:
        avg_retrieval_latency = retrieval_stats["avg"]
    if generation_stats:
        avg_generation_latency = generation_stats["avg"]
    
    return {
        "total_queries": total_queries,
        "error_rate": error_rate,
        "avg_retrieval_latency_ms": avg_retrieval_latency,
        "avg_generation_latency_ms": avg_generation_latency,
        "health_status": "healthy" if error_rate < 0.1 else "degraded"
    }