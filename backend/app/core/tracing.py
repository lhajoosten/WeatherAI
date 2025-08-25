"""OpenTelemetry tracing configuration for WeatherAI.

This module provides distributed tracing capabilities with OpenTelemetry,
including automatic instrumentation for FastAPI, HTTPX, and Redis operations.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

import structlog

try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = structlog.get_logger(__name__)

# Global tracer instance
_tracer: trace.Tracer | None = None
_initialized = False


def configure_tracing(
    service_name: str | None = None,
    otlp_endpoint: str | None = None,
    environment: str | None = None,
    console_exporter: bool = False
) -> trace.Tracer | None:
    """Configure OpenTelemetry tracing.
    
    Args:
        service_name: Service name for tracing (defaults to SERVICE_NAME env var)
        otlp_endpoint: OTLP endpoint for trace export (defaults to OTLP_ENDPOINT env var)
        environment: Environment name (defaults to ENVIRONMENT env var)
        console_exporter: Whether to add console exporter for debugging
        
    Returns:
        Configured tracer instance or None if OpenTelemetry is not available
    """
    global _tracer, _initialized
    
    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not available, tracing disabled")
        return None
    
    if _initialized:
        logger.debug("Tracing already initialized")
        return _tracer
    
    # Get configuration from environment
    service_name = service_name or os.getenv("SERVICE_NAME", "weatherai-backend")
    environment = environment or os.getenv("ENVIRONMENT", "development")
    otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT")
    
    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": os.getenv("SERVICE_VERSION", "0.1.0"),
        "deployment.environment": environment,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Add span processors
    processors_added = False
    
    # Add OTLP exporter if endpoint is configured
    if otlp_endpoint:
        try:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
            processors_added = True
            logger.info("OTLP span exporter configured", endpoint=otlp_endpoint)
        except Exception as e:
            logger.error("Failed to configure OTLP exporter", error=str(e))
    
    # Add console exporter for debugging or if no other exporter is configured
    if console_exporter or (not processors_added and environment == "development"):
        console_exporter_instance = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter_instance))
        logger.info("Console span exporter configured")
        processors_added = True
    
    if not processors_added:
        logger.warning("No span processors configured, traces will not be exported")
    
    # Get tracer instance
    _tracer = trace.get_tracer(__name__)
    _initialized = True
    
    logger.info("OpenTelemetry tracing configured", service_name=service_name, environment=environment)
    return _tracer


def get_tracer() -> trace.Tracer | None:
    """Get the configured tracer instance."""
    return _tracer


def instrument_app(app) -> None:
    """Instrument FastAPI application with OpenTelemetry.
    
    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE or not _initialized:
        logger.debug("Skipping FastAPI instrumentation - OpenTelemetry not available or not initialized")
        return
    
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.error("Failed to instrument FastAPI", error=str(e))


def instrument_httpx() -> None:
    """Instrument HTTPX client with OpenTelemetry."""
    if not OTEL_AVAILABLE or not _initialized:
        logger.debug("Skipping HTTPX instrumentation - OpenTelemetry not available or not initialized")
        return
    
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumented with OpenTelemetry")
    except Exception as e:
        logger.error("Failed to instrument HTTPX", error=str(e))


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    set_status_on_exception: bool = True
) -> Generator[trace.Span | None, None, None]:
    """Create a traced span context manager.
    
    Args:
        name: Span name
        attributes: Optional span attributes
        set_status_on_exception: Whether to set error status on exceptions
        
    Yields:
        The created span or None if tracing is not available
    """
    if not _tracer:
        yield None
        return
    
    with _tracer.start_as_current_span(name) as span:
        try:
            # Set attributes if provided
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            yield span
            
        except Exception as e:
            if set_status_on_exception and span:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def add_span_attribute(key: str, value: Any) -> None:
    """Add attribute to current span if available.
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    if not OTEL_AVAILABLE:
        return
        
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.set_attribute(key, str(value))


def add_span_event(name: str, attributes: dict[str, Any] | None = None) -> None:
    """Add event to current span if available.
    
    Args:
        name: Event name
        attributes: Optional event attributes
    """
    if not OTEL_AVAILABLE:
        return
        
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(name, attributes or {})


def get_current_trace_id() -> str | None:
    """Get the current trace ID as a string.
    
    Returns:
        Trace ID string or None if no active trace
    """
    if not OTEL_AVAILABLE:
        return None
        
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        return f"{current_span.get_span_context().trace_id:032x}"
    
    return None


def get_current_span_id() -> str | None:
    """Get the current span ID as a string.
    
    Returns:
        Span ID string or None if no active span
    """
    if not OTEL_AVAILABLE:
        return None
        
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        return f"{current_span.get_span_context().span_id:016x}"
    
    return None


# Convenience function for RAG pipeline tracing
@contextmanager
def trace_rag_operation(
    operation: str,
    query: str | None = None,
    user_id: str | None = None
) -> Generator[trace.Span | None, None, None]:
    """Create a traced span for RAG operations.
    
    Args:
        operation: RAG operation name (e.g., 'retrieval', 'generation', 'embeddings')
        query: Optional query text (truncated for privacy)
        user_id: Optional user identifier
        
    Yields:
        The created span or None if tracing is not available
    """
    attributes = {
        "rag.operation": operation,
        "component": "rag",
    }
    
    if query:
        # Truncate query for privacy and span attribute limits
        attributes["rag.query_preview"] = query[:100] + "..." if len(query) > 100 else query
        attributes["rag.query_length"] = len(query)
    
    if user_id:
        attributes["user.id"] = user_id
    
    with trace_span(f"rag.{operation}", attributes) as span:
        yield span


# Convenience function for LLM operations tracing
@contextmanager  
def trace_llm_operation(
    model: str,
    operation: str = "completion",
    provider: str = "openai"
) -> Generator[trace.Span | None, None, None]:
    """Create a traced span for LLM operations.
    
    Args:
        model: LLM model name
        operation: Operation type (e.g., 'completion', 'embedding')
        provider: LLM provider name
        
    Yields:
        The created span or None if tracing is not available
    """
    attributes = {
        "llm.provider": provider,
        "llm.model": model,
        "llm.operation": operation,
        "component": "llm",
    }
    
    with trace_span(f"llm.{operation}", attributes) as span:
        yield span