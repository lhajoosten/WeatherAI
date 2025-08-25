"""
RAG (Retrieval Augmented Generation) Pipeline Implementation.

This module provides a foundational RAG pipeline with the following components:
- Document chunking and preprocessing
- Text embedding generation
- Vector storage and similarity search
- Retrieval with optional MMR re-ranking
- Prompt building and LLM generation
- Caching for embeddings and answers
- Metrics and guardrails

The pipeline is designed to be modular and extensible while maintaining
clean abstractions between components.
"""

from .exceptions import RAGError, LowSimilarityError, EmptyContextError, CacheMissError
from .models import (
    Document,
    Chunk,
    RetrievedChunk,
    EmbeddingResult,
    GenerationResult,
    AnswerResult,
    PromptParts,
)

__all__ = [
    "RAGError",
    "LowSimilarityError", 
    "EmptyContextError",
    "CacheMissError",
    "Document",
    "Chunk",
    "RetrievedChunk",
    "EmbeddingResult",
    "GenerationResult",
    "AnswerResult",
    "PromptParts",
]