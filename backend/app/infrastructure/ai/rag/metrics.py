"""Enhanced metrics for RAG pipeline - Phase 5 with unified observability."""

import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
import structlog

from app.core.metrics import record_metric
from app.core.tracing import trace_rag_operation, add_span_attribute, add_span_event
from app.core.logging import get_rag_logger, get_correlation_context
from app.core.constants import PROMPT_VERSION

logger = get_rag_logger(__name__)

# Phase 5 metric names (Prometheus/OTel compatible)
RAG_RETRIEVAL_LATENCY = "rag_retrieval_latency_ms"
RAG_TOPK = "rag_topk"
LLM_TOKENS_IN = "llm_tokens_in"
LLM_TOKENS_OUT = "llm_tokens_out"
RAG_CACHE_HIT = "rag_cache_hit"
RAG_GUARDRAIL_TRIGGERED = "rag_guardrail_triggered"
RATE_LIMIT_EVENTS = "rate_limit_events"


@asynccontextmanager
async def time_retrieval(query: str | None = None, user_id: str | None = None):
    """Time retrieval operations and record metrics with tracing."""
    start_time = time.time()
    
    with trace_rag_operation("retrieval", query=query, user_id=user_id) as span:
        try:
            if span:
                add_span_attribute("rag.stage", "retrieval")
                add_span_event("retrieval_started")
            
            yield
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            record_metric(RAG_RETRIEVAL_LATENCY, duration_ms, {"stage": "retrieval"})
            record_metric("rag.retrieval.duration_seconds", duration_ms / 1000, {"stage": "retrieval"})
            
            # Add tracing attributes
            if span:
                add_span_attribute("rag.retrieval.duration_ms", duration_ms)
                add_span_event("retrieval_completed", {"duration_ms": duration_ms})
            
            # Log completion
            correlation = get_correlation_context()
            logger.info(
                "RAG retrieval completed",
                duration_ms=duration_ms,
                stage="retrieval",
                **correlation
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record error metrics
            record_metric("rag.retrieval.errors.total", 1, {
                "error_type": type(e).__name__,
                "stage": "retrieval"
            })
            
            # Add tracing error
            if span:
                add_span_attribute("rag.error", True)
                add_span_attribute("rag.error_type", type(e).__name__)
                add_span_event("retrieval_failed", {
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:200]  # Truncate for span limits
                })
            
            # Log error
            correlation = get_correlation_context()
            logger.error(
                "RAG retrieval failed",
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                stage="retrieval",
                **correlation
            )
            
            raise


@asynccontextmanager
async def time_generation(model: str | None = None, user_id: str | None = None):
    """Time generation operations and record metrics with tracing."""
    start_time = time.time()
    
    with trace_rag_operation("generation", user_id=user_id) as span:
        try:
            if span:
                add_span_attribute("rag.stage", "generation")
                if model:
                    add_span_attribute("llm.model", model)
                add_span_event("generation_started")
            
            yield
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Record metrics
            record_metric("rag.generation.duration_seconds", duration_ms / 1000, {
                "stage": "generation",
                "model": model or "unknown"
            })
            
            # Add tracing attributes
            if span:
                add_span_attribute("rag.generation.duration_ms", duration_ms)
                add_span_event("generation_completed", {"duration_ms": duration_ms})
            
            # Log completion
            correlation = get_correlation_context()
            logger.info(
                "RAG generation completed",
                duration_ms=duration_ms,
                model=model,
                stage="generation",
                **correlation
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Record error metrics
            record_metric("rag.generation.errors.total", 1, {
                "error_type": type(e).__name__,
                "stage": "generation",
                "model": model or "unknown"
            })
            
            # Add tracing error
            if span:
                add_span_attribute("rag.error", True)
                add_span_attribute("rag.error_type", type(e).__name__)
                add_span_event("generation_failed", {
                    "error_type": type(e).__name__,
                    "error_message": str(e)[:200]
                })
            
            # Log error
            correlation = get_correlation_context()
            logger.error(
                "RAG generation failed",
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                model=model,
                stage="generation",
                **correlation
            )
            
            raise


def record_rag_topk(k_value: int, user_id: str | None = None) -> None:
    """Record the top-k value used in retrieval with enhanced observability."""
    record_metric(RAG_TOPK, float(k_value), {"component": "rag", "metric_type": "configuration"})
    
    # Add to tracing if active
    add_span_attribute("rag.top_k", k_value)
    
    # Log with correlation
    correlation = get_correlation_context()
    logger.debug(
        "RAG top-k configured",
        top_k=k_value,
        component="rag",
        **correlation
    )


def record_llm_tokens(tokens_in: int, tokens_out: int, model: str | None = None) -> None:
    """Record LLM token usage with enhanced observability."""
    tags = {"component": "rag", "model": model or "unknown"}
    
    record_metric(LLM_TOKENS_IN, float(tokens_in), tags)
    record_metric(LLM_TOKENS_OUT, float(tokens_out), tags)
    record_metric("llm.tokens.total", float(tokens_in + tokens_out), tags)
    
    # Add to tracing if active
    add_span_attribute("llm.tokens.input", tokens_in)
    add_span_attribute("llm.tokens.output", tokens_out)
    add_span_attribute("llm.tokens.total", tokens_in + tokens_out)
    if model:
        add_span_attribute("llm.model", model)
    
    # Log with correlation
    correlation = get_correlation_context()
    logger.info(
        "LLM token usage recorded",
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        tokens_total=tokens_in + tokens_out,
        model=model,
        component="rag",
        **correlation
    )


def record_cache_hit(cache_type: str, hit: bool, duration_ms: Optional[float] = None) -> None:
    """Record cache hit/miss with enhanced observability."""
    tags = {"cache_type": cache_type, "hit": str(hit).lower(), "component": "rag"}
    
    record_metric(RAG_CACHE_HIT, 1.0, tags)
    
    if duration_ms is not None:
        record_metric("rag.cache.duration_ms", duration_ms, tags)
    
    # Add to tracing if active  
    add_span_attribute(f"rag.cache.{cache_type}.hit", hit)
    if duration_ms is not None:
        add_span_attribute(f"rag.cache.{cache_type}.duration_ms", duration_ms)
    
    # Log with correlation
    correlation = get_correlation_context()
    logger.debug(
        "Cache operation recorded",
        cache_type=cache_type,
        hit=hit,
        duration_ms=duration_ms,
        component="rag",
        **correlation
    )


def record_guardrail_trigger(guardrail_type: str, triggered: bool, reason: str | None = None) -> None:
    """Record guardrail activation with enhanced observability."""
    tags = {"guardrail_type": guardrail_type, "triggered": str(triggered).lower(), "component": "rag"}
    
    record_metric(RAG_GUARDRAIL_TRIGGERED, 1.0, tags)
    
    # Add to tracing if active
    add_span_attribute(f"rag.guardrail.{guardrail_type}.triggered", triggered)
    if reason:
        add_span_attribute(f"rag.guardrail.{guardrail_type}.reason", reason[:100])  # Truncate for span limits
    
    # Log with correlation
    correlation = get_correlation_context()
    log_level = "warning" if triggered else "debug"
    log_event = "Guardrail triggered" if triggered else "Guardrail passed"
    
    getattr(logger, log_level)(
        log_event,
        guardrail_type=guardrail_type,
        triggered=triggered,
        reason=reason,
        component="rag",
        **correlation
    )


def record_rate_limit_event(endpoint: str, user_id: str | None = None, exceeded: bool = True) -> None:
    """Record rate limiting events with enhanced observability."""
    tags = {"endpoint": endpoint, "exceeded": str(exceeded).lower(), "component": "rag"}
    
    record_metric(RATE_LIMIT_EVENTS, 1.0, tags)
    
    # Add to tracing if active
    add_span_attribute("rag.rate_limit.exceeded", exceeded)
    add_span_attribute("rag.rate_limit.endpoint", endpoint)
    
    # Log with correlation
    correlation = get_correlation_context()
    logger.warning(
        "Rate limit event",
        endpoint=endpoint,
        exceeded=exceeded,
        user_id=user_id,
        component="rag",
        **correlation
    )


def estimate_cost(tokens_in: int, tokens_out: int, model: str = "gpt-4") -> float:
    """Estimate cost for LLM usage based on token counts.
    
    Args:
        tokens_in: Input tokens
        tokens_out: Output tokens  
        model: Model name for pricing
        
    Returns:
        Estimated cost in USD
    """
    # Simplified cost estimation - would be enhanced with real pricing data
    cost_per_1k_input = {
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.001,
    }
    
    cost_per_1k_output = {
        "gpt-4": 0.06,
        "gpt-4-turbo": 0.03,
        "gpt-3.5-turbo": 0.002,
    }
    
    input_rate = cost_per_1k_input.get(model, cost_per_1k_input["gpt-4"])
    output_rate = cost_per_1k_output.get(model, cost_per_1k_output["gpt-4"])
    
    cost = (tokens_in * input_rate / 1000) + (tokens_out * output_rate / 1000)
    return round(cost, 6)


def log_pipeline_metrics(
    query: str,
    num_retrieved: int,
    num_filtered: int,
    min_similarity: float,
    context_tokens: int,
    cache_hits: Dict[str, bool],
    retrieval_latency_ms: Optional[float] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    model: Optional[str] = None,
    user_id: Optional[str] = None,
    cost_estimate: Optional[float] = None
) -> None:
    """Log comprehensive pipeline metrics with Phase 5 observability enhancements."""
    
    # Record individual metrics with enhanced observability
    record_rag_topk(num_retrieved, user_id=user_id)
    
    if tokens_in and tokens_out:
        record_llm_tokens(tokens_in, tokens_out, model=model)
        
        # Calculate cost if not provided
        if cost_estimate is None and model:
            cost_estimate = estimate_cost(tokens_in, tokens_out, model)
    
    # Record cache metrics with timing if available
    for cache_type, hit in cache_hits.items():
        record_cache_hit(cache_type, hit)
    
    # Record comprehensive metrics
    pipeline_tags = {"component": "rag", "stage": "pipeline_complete"}
    record_metric("rag.pipeline.queries.total", 1.0, pipeline_tags)
    record_metric("rag.pipeline.documents.retrieved", float(num_retrieved), pipeline_tags)
    record_metric("rag.pipeline.documents.filtered", float(num_filtered), pipeline_tags)
    record_metric("rag.pipeline.similarity.min", min_similarity, pipeline_tags)
    record_metric("rag.pipeline.context.tokens", float(context_tokens), pipeline_tags)
    
    if retrieval_latency_ms:
        record_metric("rag.pipeline.retrieval.latency_ms", retrieval_latency_ms, pipeline_tags)
    
    if cost_estimate:
        record_metric("rag.pipeline.cost.estimated_usd", cost_estimate, {**pipeline_tags, "model": model or "unknown"})
    
    # Add tracing attributes
    add_span_attribute("rag.pipeline.documents_retrieved", num_retrieved)
    add_span_attribute("rag.pipeline.documents_filtered", num_filtered)
    add_span_attribute("rag.pipeline.similarity_threshold", min_similarity)
    add_span_attribute("rag.pipeline.context_tokens", context_tokens)
    
    if cost_estimate:
        add_span_attribute("rag.pipeline.estimated_cost_usd", cost_estimate)
    
    if retrieval_latency_ms:
        add_span_attribute("rag.pipeline.retrieval_latency_ms", retrieval_latency_ms)
    
    # Cache hit summary for tracing
    cache_hit_summary = {f"cache_{k}_hit": v for k, v in cache_hits.items()}
    for attr_name, hit_value in cache_hit_summary.items():
        add_span_attribute(f"rag.{attr_name}", hit_value)
    
    # Add span event for pipeline completion
    add_span_event("rag_pipeline_completed", {
        "documents_retrieved": num_retrieved,
        "documents_filtered": num_filtered,
        "context_tokens": context_tokens,
        "cost_usd": cost_estimate or 0.0
    })
    
    # Enhanced structured logging with correlation
    correlation = get_correlation_context()
    
    logger.info(
        "RAG pipeline completed",
        event="rag_pipeline_completed",
        query_hash=hash(query) % (10**8),  # Simple hash for grouping
        truncated_query=query[:120],  # First 120 chars for privacy
        num_retrieved=num_retrieved,
        num_filtered=num_filtered,
        min_similarity=min_similarity,
        context_tokens=context_tokens,
        retrieval_latency_ms=retrieval_latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        model=model,
        cost_estimate_usd=cost_estimate,
        prompt_version=PROMPT_VERSION,
        cache_hits=cache_hits,
        component="rag",
        **correlation
    )


def record_pipeline_error(
    error_type: str, 
    stage: str, 
    query: Optional[str] = None,
    user_id: Optional[str] = None,
    error_message: Optional[str] = None
) -> None:
    """Record pipeline errors with enhanced observability."""
    tags = {
        "error_type": error_type, 
        "stage": stage, 
        "component": "rag"
    }
    
    record_metric("rag.pipeline.errors.total", 1.0, tags)
    
    # Add tracing attributes
    add_span_attribute("rag.error", True)
    add_span_attribute("rag.error_type", error_type)
    add_span_attribute("rag.error_stage", stage)
    
    # Add span event for error
    add_span_event("rag_pipeline_error", {
        "error_type": error_type,
        "stage": stage,
        "error_message": error_message[:200] if error_message else None
    })
    
    # Enhanced error logging with correlation
    correlation = get_correlation_context()
    
    logger.error(
        "RAG pipeline error",
        error_type=error_type,
        stage=stage,
        error_message=error_message,
        query_hash=hash(query) % (10**8) if query else None,
        truncated_query=query[:120] if query else None,
        component="rag",
        **correlation
    )
    
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