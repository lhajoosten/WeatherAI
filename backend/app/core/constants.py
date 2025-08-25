"""Core constants for WeatherAI application."""

# RAG Prompt versioning for Phase 4
PROMPT_VERSION = "v1"

# RAG Streaming event types
class RAGStreamEventType:
    """Event types for RAG streaming responses."""
    TOKEN = "token"
    DONE = "done"
    ERROR = "error"

# Domain error codes for frontend i18n mapping
class DomainErrorCode:
    """Error codes that map to frontend internationalization keys."""
    RATE_LIMITED = "rate_limited"
    VALIDATION_ERROR = "validation_error"
    NO_CONTEXT = "no_context"
    RETRIEVAL_TIMEOUT = "retrieval_timeout"
    INTERNAL_ERROR = "internal_error"

# Cache key prefixes
class CachePrefix:
    """Standardized cache key prefixes."""
    EMBEDDING = "embed"
    RAG_ANSWER = "rag:qa"
    RATE_LIMIT_STREAM = "rl:rag_stream"