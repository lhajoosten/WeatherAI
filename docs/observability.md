# WeatherAI Backend Observability

This document describes the comprehensive observability infrastructure implemented in Phase 5 of the WeatherAI backend, including logging, metrics, and tracing capabilities.

## Overview

The observability stack consists of three main pillars:

1. **Structured Logging**: JSON-formatted logs with correlation IDs and contextual information
2. **Metrics**: Prometheus-compatible metrics for monitoring system health and performance  
3. **Tracing**: OpenTelemetry-based distributed tracing for request flow visibility

## Architecture

### Core Components

- `app/core/logging.py` - Centralized logging configuration with correlation context
- `app/core/metrics.py` - Unified metrics interface with Prometheus export
- `app/core/tracing.py` - OpenTelemetry tracing setup and instrumentation
- `app/core/middleware.py` - Unified observability middleware for HTTP requests

### Correlation IDs

All observability data is correlated using three context variables:

- **request_id**: Unique identifier for each HTTP request
- **trace_id**: Distributed tracing identifier (from OpenTelemetry or request_id fallback)
- **user_id**: User identifier when available (extracted from authentication)

## Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
JSON_LOGS=true                    # Enable JSON log format
SERVICE_NAME=weatherai-backend    # Service identifier

# Metrics  
ENABLE_PROMETHEUS_METRICS=true   # Enable Prometheus metrics
METRICS_AUTH_TOKEN=secret123      # Optional bearer token for /metrics endpoint

# Tracing
ENABLE_TRACING=true              # Enable OpenTelemetry tracing  
OTLP_ENDPOINT=http://jaeger:4317 # OTLP gRPC endpoint for trace export
TRACE_SAMPLE_RATE=1.0            # Sampling rate (0.0-1.0)

# Cost Tracking
ENABLE_COST_TRACKING=true        # Enable LLM cost estimation
COST_TRACKING_SAMPLING_RATE=1.0  # Cost tracking sampling rate

# Environment
ENVIRONMENT=production           # Environment name (development, staging, production)
```

### FastAPI Integration

The observability middleware is automatically added to FastAPI:

```python
from app.core.middleware import ObservabilityMiddleware

app.add_middleware(
    ObservabilityMiddleware,
    service_name="weatherai-backend",
    exclude_paths=["/health", "/metrics", "/docs"]
)
```

## Logging

### Structured Format

All logs are emitted in JSON format with consistent fields:

```json
{
  "timestamp": "2025-08-25T20:30:45.123456Z",
  "level": "info",
  "logger": "app.api.v1.routes.rag",
  "event": "RAG query completed",
  "service": "weatherai-backend", 
  "environment": "production",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "trace_id": "abcd1234567890ef",
  "user_id": "user123",
  "component": "rag",
  "query_hash": 12345678,
  "duration_ms": 1250,
  "tokens_in": 150,
  "tokens_out": 75
}
```

### Component Loggers

Use tagged loggers for different components:

```python
from app.core.logging import get_api_logger, get_rag_logger, get_llm_logger

# Component-specific loggers
api_logger = get_api_logger(__name__)
rag_logger = get_rag_logger(__name__)
llm_logger = get_llm_logger(__name__)

# Usage
rag_logger.info("Query processed", tokens=150, duration_ms=1250)
```

### Correlation Context

Set correlation IDs manually when needed:

```python
from app.core.logging import set_correlation_id, get_correlation_context

# Set context
set_correlation_id(request_id="req-123", user_id="user-456")

# Get current context
context = get_correlation_context()
logger.info("Processing request", **context)
```

## Metrics

### Prometheus Export

Metrics are available at `/metrics` endpoint in Prometheus format:

```bash
# Without authentication
curl http://localhost:8000/api/metrics

# With bearer token (if METRICS_AUTH_TOKEN is set)
curl -H "Authorization: Bearer secret123" http://localhost:8000/api/metrics
```

### Available Metrics

#### HTTP Metrics
- `http_requests_total{method, endpoint, status_code}` - Total HTTP requests
- `http_request_duration_seconds{method, endpoint}` - Request duration histogram
- `http_responses_total{method, status_category}` - Response count by status category
- `http_errors_total{method, status_code}` - Error count by status code

#### LLM Metrics
- `llm_requests_total{model, provider}` - Total LLM requests
- `llm_tokens_total{model, type}` - Token consumption (input/output)
- `llm_request_duration_seconds{model, provider}` - LLM request duration

#### RAG Metrics
- `rag_queries_total{cache_hit}` - Total RAG queries
- `rag_retrieval_duration_seconds` - Document retrieval duration
- `rag_documents_retrieved` - Number of documents retrieved
- `rag_pipeline_cost_estimated_usd{model}` - Estimated cost per query

#### Cache Metrics
- `cache_operations_total{operation, cache_type, hit}` - Cache operations
- `cache_operation_duration_seconds{operation, cache_type}` - Cache operation duration

### Custom Metrics

Record custom metrics using the unified interface:

```python
from app.core.metrics import record_metric

# Counter metrics
record_metric("custom.counter", 1.0, {"component": "myservice"})

# Duration metrics (automatically become histograms)
record_metric("custom.duration_seconds", 0.125, {"operation": "process"})

# Gauge metrics  
record_metric("custom.queue_size", 42.0, {"queue": "primary"})
```

## Tracing

### OpenTelemetry Integration

Tracing automatically instruments:

- **FastAPI**: All HTTP requests with spans
- **HTTPX**: Outbound HTTP requests
- **Manual spans**: Custom business logic tracing

### RAG Pipeline Tracing

The RAG pipeline includes detailed tracing:

```python
from app.core.tracing import trace_rag_operation, trace_llm_operation

# RAG operation tracing
async with trace_rag_operation("retrieval", query=query, user_id=user_id) as span:
    documents = await retriever.retrieve(query)
    if span:
        span.set_attribute("documents_found", len(documents))

# LLM operation tracing  
async with trace_llm_operation("gpt-4", "completion") as span:
    response = await llm.generate(prompt)
    if span:
        span.set_attribute("tokens_generated", response.tokens)
```

### Manual Spans

Create custom spans for business logic:

```python
from app.core.tracing import trace_span, add_span_attribute, add_span_event

async with trace_span("business_logic", {"operation": "forecast"}) as span:
    add_span_event("processing_started")
    result = await process_forecast()
    add_span_attribute("forecast_accuracy", result.accuracy)
    add_span_event("processing_completed")
```

### Trace Export

Configure trace export to your observability backend:

```bash
# Jaeger
OTLP_ENDPOINT=http://jaeger:4317

# Other OTLP-compatible backends
OTLP_ENDPOINT=https://api.honeycomb.io:443
OTLP_ENDPOINT=https://ingest.lightstep.com:443
```

## RAG Pipeline Observability

### Enhanced Metrics

The RAG pipeline includes comprehensive observability:

```python
from app.infrastructure.ai.rag.metrics import (
    time_retrieval,
    time_generation, 
    log_pipeline_metrics,
    record_cache_hit,
    record_guardrail_trigger
)

# Timed operations with correlation
async with time_retrieval(query=query, user_id=user_id):
    documents = await retrieve_documents(query)

async with time_generation(model="gpt-4", user_id=user_id):
    answer = await generate_answer(context, query)

# Comprehensive pipeline metrics
log_pipeline_metrics(
    query=query,
    num_retrieved=len(documents),
    num_filtered=len(filtered_docs),
    min_similarity=0.75,
    context_tokens=context_token_count,
    cache_hits={"embeddings": True, "answers": False},
    retrieval_latency_ms=retrieval_time,
    tokens_in=prompt_tokens,
    tokens_out=completion_tokens,
    model="gpt-4",
    user_id=user_id
)
```

### Cost Tracking

Automatic cost estimation for LLM usage:

```python
from app.infrastructure.ai.rag.metrics import estimate_cost

# Automatic cost calculation
cost_usd = estimate_cost(tokens_in=150, tokens_out=75, model="gpt-4")
# Returns: 0.0045 (estimated USD)
```

### Sampling

For high-volume endpoints, implement sampling:

```python
import random
from app.core.config import get_settings

settings = get_settings()

# Sample based on configuration
if random.random() < settings.cost_tracking_sampling_rate:
    log_pipeline_metrics(...)  # Only log subset of events
```

## Dashboard and Alerting

### Grafana Dashboards

Key metrics to monitor:

1. **Request Volume**: `rate(http_requests_total[5m])`
2. **Error Rate**: `rate(http_errors_total[5m]) / rate(http_requests_total[5m])`
3. **Response Time**: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
4. **LLM Token Usage**: `rate(llm_tokens_total[1h])`
5. **LLM Cost**: `rate(rag_pipeline_cost_estimated_usd[1h])`
6. **Cache Hit Rate**: `rate(cache_operations_total{hit="true"}[5m]) / rate(cache_operations_total[5m])`

### Alerting Rules

Recommended Prometheus alerting rules:

```yaml
groups:
- name: weatherai-backend
  rules:
  - alert: HighErrorRate
    expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.05
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      
  - alert: HighLLMCosts
    expr: rate(rag_pipeline_cost_estimated_usd[1h]) > 10.0
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "LLM costs exceeding $10/hour"
```

## Development and Testing

### Local Development

For local development, observability works with minimal configuration:

```bash
# Basic logging to console
LOG_LEVEL=DEBUG
JSON_LOGS=false

# Disable external dependencies  
ENABLE_PROMETHEUS_METRICS=true
ENABLE_TRACING=false  # Will fallback gracefully
```

### Testing

Mock observability components in tests:

```python
from app.core.metrics import get_metrics_sink
from app.core.logging import configure_logging

def test_with_observability():
    # Reset metrics
    get_metrics_sink().clear()
    
    # Your test code
    result = await my_function()
    
    # Verify metrics were recorded
    metrics = get_metrics_sink().get_metrics("custom.counter")
    assert len(metrics) == 1
```

## Troubleshooting

### Common Issues

1. **Missing Correlation IDs**: Ensure ObservabilityMiddleware is added before other middleware
2. **Metrics Not Appearing**: Check `ENABLE_PROMETHEUS_METRICS=true` and `/metrics` endpoint
3. **Traces Not Exported**: Verify `OTLP_ENDPOINT` and network connectivity
4. **High Memory Usage**: Reduce `TRACE_SAMPLE_RATE` or implement sampling

### Debug Information

Enable debug logging to troubleshoot observability:

```bash
LOG_LEVEL=DEBUG
```

This will show internal observability operations and help identify configuration issues.

## Security Considerations

1. **PII in Logs**: Query text is truncated to 120 characters and hashed for grouping
2. **Metrics Authentication**: Use `METRICS_AUTH_TOKEN` to protect `/metrics` endpoint  
3. **Trace Data**: Avoid including sensitive data in span attributes
4. **Cost Information**: Consider access controls for cost metrics in production

## Performance Impact

The observability infrastructure is designed for minimal performance impact:

- **Logging**: Async structured logging with configurable levels
- **Metrics**: In-memory collection with periodic export
- **Tracing**: Configurable sampling rates to control overhead
- **Correlation**: Context variables avoid thread-local storage overhead

Typical performance overhead: <5% latency increase, <50MB memory increase.