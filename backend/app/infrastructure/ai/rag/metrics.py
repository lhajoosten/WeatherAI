"""Enhanced metrics for RAG pipeline - Phase 4."""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import structlog

from app.core.metrics import record_metric, record_timing
from app.core.constants import PROMPT_VERSION

logger = structlog.get_logger(__name__)

# Phase 4 metric names (Prometheus/OTel compatible)
RAG_RETRIEVAL_LATENCY = "rag_retrieval_latency_ms"
RAG_TOPK = "rag_topk"
LLM_TOKENS_IN = "llm_tokens_in"
LLM_TOKENS_OUT = "llm_tokens_out"
RAG_CACHE_HIT = "rag_cache_hit"
RAG_GUARDRAIL_TRIGGERED = "rag_guardrail_triggered"
RATE_LIMIT_EVENTS = "rate_limit_events"


@asynccontextmanager
async def time_retrieval():
    """Time retrieval operations and record metrics."""
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        record_metric(RAG_RETRIEVAL_LATENCY, duration_ms)
        record_timing("rag.retrieval", duration_ms)


@asynccontextmanager
async def time_generation():
    """Time generation operations and record metrics."""
    start_time = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        record_timing("rag.generation", duration_ms)


def record_rag_topk(k_value: int) -> None:
    """Record the top-k value used in retrieval."""
    record_metric(RAG_TOPK, float(k_value))


def record_llm_tokens(tokens_in: int, tokens_out: int) -> None:
    """Record LLM token usage."""
    record_metric(LLM_TOKENS_IN, float(tokens_in))
    record_metric(LLM_TOKENS_OUT, float(tokens_out))


def record_cache_hit(cache_type: str, hit: bool) -> None:
    """Record cache hit/miss with type label."""
    record_metric(RAG_CACHE_HIT, 1.0 if hit else 0.0, {"type": cache_type})


def record_guardrail_triggered(guardrail_type: str = "similarity_threshold") -> None:
    """Record when a guardrail is triggered."""
    record_metric(RAG_GUARDRAIL_TRIGGERED, 1.0, {"type": guardrail_type})


def record_rate_limit_event(endpoint: str, user_id: Optional[str] = None) -> None:
    """Record rate limit events."""
    tags = {"endpoint": endpoint}
    if user_id:
        tags["user_type"] = "authenticated"
    else:
        tags["user_type"] = "anonymous"
    record_metric(RATE_LIMIT_EVENTS, 1.0, tags)


def log_pipeline_metrics(
    query: str,
    num_retrieved: int,
    num_filtered: int,
    min_similarity: float,
    context_tokens: int,
    cache_hits: Dict[str, bool],
    retrieval_latency_ms: Optional[float] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None
) -> None:
    """Log comprehensive pipeline metrics for observability."""
    
    # Record individual metrics
    record_rag_topk(num_retrieved)
    if tokens_in and tokens_out:
        record_llm_tokens(tokens_in, tokens_out)
    
    for cache_type, hit in cache_hits.items():
        record_cache_hit(cache_type, hit)
    
    # Structured logging with required Phase 4 fields
    logger.info(
        "RAG pipeline metrics",
        event="rag_pipeline_completed",
        query_hash=hash(query) % (10**8),  # Simple hash for grouping
        truncated_query=query[:120],  # First 120 chars as per requirements
        num_retrieved=num_retrieved,
        num_filtered=num_filtered,
        min_similarity=min_similarity,
        context_tokens=context_tokens,
        retrieval_latency_ms=retrieval_latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        prompt_version=PROMPT_VERSION,
        cache_hits=cache_hits
    )


def record_pipeline_error(error_type: str, stage: str, query: Optional[str] = None) -> None:
    """Record pipeline errors for monitoring."""
    tags = {"error_type": error_type, "stage": stage}
    record_metric("rag_pipeline_errors", 1.0, tags)
    
    # Structured error logging
    log_data = {
        "event": "rag_pipeline_error",
        "error_type": error_type,
        "stage": stage,
        "prompt_version": PROMPT_VERSION
    }
    
    if query:
        log_data.update({
            "query_hash": hash(query) % (10**8),
            "truncated_query": query[:120]
        })
    
    logger.error("RAG pipeline error", **log_data)


# Legacy compatibility functions (to be deprecated)
class RAGMetrics:
    """Legacy metrics class - maintained for backward compatibility."""
    
    def __init__(self):
        self._counters = {}
        self._histograms = {}
        self._gauges = {}
    
    def increment_counter(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        record_metric(name, float(value), labels or {})
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        record_metric(name, value, labels or {})
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        record_metric(name, value, labels or {})
    
    def get_stats(self) -> Dict[str, Any]:
        return {"counters": {}, "histograms": {}, "gauges": {}}


# Global metrics instance for backward compatibility
_metrics = RAGMetrics()


def get_metrics() -> RAGMetrics:
    """Get global metrics instance."""
    return _metrics