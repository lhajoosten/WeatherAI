"""Domain exceptions for RAG pipeline."""


class RAGError(Exception):
    """Base exception for RAG pipeline errors."""
    pass


class LowSimilarityError(RAGError):
    """Raised when retrieved documents have similarity below threshold."""
    
    def __init__(self, threshold: float, max_similarity: float | None = None):
        self.threshold = threshold
        self.max_similarity = max_similarity
        message = f"All retrieved documents below similarity threshold {threshold}"
        if max_similarity is not None:
            message += f" (max similarity: {max_similarity:.3f})"
        super().__init__(message)


class EmptyContextError(RAGError):
    """Raised when no context is available for generation."""
    pass


class CacheMissError(RAGError):
    """Raised when expected cache hit fails."""
    pass