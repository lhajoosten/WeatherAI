# ADR-004: RAG Streaming Architecture with Enhanced Observability

**Status:** Accepted  
**Date:** 2024-08-25  
**Authors:** WeatherAI Team (Phase 4 Implementation)

## Context

Phase 4 of WeatherAI backend requires implementing real-time RAG answer streaming with professional-grade observability, caching, and resilience features. The frontend has evolved to support real-time interactions, and users expect low-latency responses with proper error handling and i18n support.

## Decision

We implemented a comprehensive RAG streaming architecture with the following components:

### 1. Server-Sent Events (SSE) Streaming
- **Endpoint:** `POST /rag/stream`
- **Media Type:** `text/event-stream`
- **Event Types:** `token`, `done`, `error`
- **Benefits:** Standards-compliant, firewall-friendly, built-in reconnection

### 2. Enhanced Retrieval Pipeline
- **Similarity Threshold:** Lowered from 0.75 to 0.55 for better recall
- **MMR Re-ranking:** Optional diversity enhancement (λ=0.5 default)
- **Average Similarity Guardrails:** Quality gate using mean similarity scores
- **Top-K Configuration:** Increased maximum to 8 for better context

### 3. Advanced Caching Strategy
- **Embedding Cache:** `embed:{model}:{hash(text)}` with 7-day TTL
- **Answer Cache:** `rag:qa:{hash(query)}:{prompt_version}` with 1-hour TTL
- **Prompt Versioning:** Integrated `PROMPT_VERSION = "v1"` throughout pipeline
- **Model Isolation:** Separate cache keys for different embedding models

### 4. Rate Limiting for Streaming
- **Limit:** 20 requests per 5-minute window per user
- **Implementation:** Redis-based token bucket with sliding window
- **Key Pattern:** `rl:rag_stream:{user_id}`
- **Fallback:** Graceful degradation when Redis unavailable

### 5. Provider Resilience
- **Retry Logic:** 2 retries with exponential backoff (1s, 2s base delays)
- **Retryable Errors:** 429 rate limits, 5xx server errors, timeouts, connection issues
- **Error Mapping:** Domain exceptions mapped to i18n-compatible error codes

### 6. Observability & Metrics
- **Structured Logging:** JSON format with trace_id, user_id, query_hash, truncated_query
- **Metrics:** Prometheus/OTel compatible counters and histograms
- **Key Metrics:** `rag_retrieval_latency_ms`, `llm_tokens_in/out`, `rag_cache_hit`, `rag_guardrail_triggered`
- **Privacy:** Query hashing and truncation to protect user data

## Implementation Details

### Cache Key Strategy
```
# Embedding cache with model isolation
embed:{model_name}:{hash(sorted_texts)}

# Answer cache with prompt versioning  
rag:qa:{hash(normalized_query)}:{prompt_version}

# Rate limiting with user isolation
rl:rag_stream:{user_id}
```

### Error Code Mapping
- `rate_limited` → HTTP 429 + frontend display
- `validation_error` → HTTP 400 + form validation
- `no_context` → HTTP 200 + SSE done event with guardrail
- `retrieval_timeout` → HTTP 500 + retry prompt
- `internal_error` → HTTP 500 + generic error message

### Event Stream Format
```javascript
// Token events during generation
data: {"type": "token", "data": "word"}

// Completion with metadata
data: {"type": "done", "data": {"prompt_version": "v1", "sources_count": 3, "total_tokens": 150}}

// Error with i18n code
data: {"type": "error", "data": {"error_code": "validation_error", "message": "Query too long", "prompt_version": "v1"}}
```

## Alternatives Considered

### 1. WebSocket vs SSE
- **Chosen:** SSE for simplicity and unidirectional streaming needs
- **Rejected:** WebSocket (unnecessary bidirectional complexity)

### 2. Individual vs Average Similarity Thresholds
- **Chosen:** Average similarity for guardrails (better UX)
- **Rejected:** Individual chunk filtering only (too restrictive)

### 3. Cache Key Structure
- **Chosen:** Hierarchical keys with model/version isolation
- **Rejected:** Simple hash-only keys (version conflicts)

### 4. Rate Limiting Algorithms
- **Chosen:** Token bucket with Redis sliding window
- **Rejected:** Fixed window (burst issues), in-memory only (scaling issues)

## Consequences

### Positive
- **User Experience:** Real-time streaming responses feel more interactive
- **Observability:** Comprehensive metrics enable proactive monitoring
- **Scalability:** Proper caching reduces LLM costs and latency
- **Reliability:** Retry logic and graceful degradation improve availability
- **Maintainability:** Clean architecture with testable components

### Negative
- **Complexity:** More moving parts require careful monitoring
- **Redis Dependency:** Cache and rate limiting rely on Redis availability
- **Token Estimation:** Streaming makes exact token counting challenging
- **Browser Limits:** SSE connections count against browser connection limits

### Mitigations
- **Fallback Mechanisms:** In-memory rate limiting when Redis unavailable
- **Circuit Breakers:** Automatic degradation for failing components
- **Monitoring:** Comprehensive alerting on cache miss rates, error rates
- **Documentation:** Clear operational runbooks for common issues

## Testing Strategy

Comprehensive test suite covering:
- **Stream Endpoint:** SSE event ordering and error handling
- **Retrieval:** MMR re-ranking and guardrail behavior
- **Caching:** Model isolation and version compatibility
- **Rate Limiting:** Token bucket mechanics and edge cases
- **Guardrails:** Similarity threshold scenarios
- **Prompt Versioning:** Consistency across all components

## Migration Path

1. **Phase 4a:** Deploy with feature flag disabled
2. **Phase 4b:** Enable for internal testing users
3. **Phase 4c:** Gradual rollout to all users
4. **Phase 4d:** Remove legacy non-streaming endpoint

## Monitoring & Alerts

Key metrics to monitor:
- **Error Rate:** `rag_stream_errors / rag_stream_requests < 5%`
- **Latency:** `p95(rag_retrieval_latency_ms) < 2000ms`
- **Cache Hit Rate:** `rag_cache_hit_rate > 30%`
- **Rate Limit Events:** Monitor for abuse patterns
- **Guardrail Triggers:** Track content quality issues

## Future Considerations

- **Multi-Model Support:** Easy addition of new embedding models
- **Advanced MMR:** Store embeddings with chunks for better diversity
- **Streaming LLM:** Replace simulated streaming with actual model streaming
- **Regional Scaling:** Distribute caches across geographic regions
- **A/B Testing:** Framework for testing different similarity thresholds

---

**References:**
- [Phase 3C Summary](../PHASE_3C_SUMMARY.md)
- [Configuration Guide](../docs/config.md)
- [Prompt Templates](../../docs/PROMPTS.md)
- [Test Coverage Report](../tests/)