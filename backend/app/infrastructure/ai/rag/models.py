"""Core data models for RAG pipeline."""

from dataclasses import dataclass
from typing import Any, Dict, List
from uuid import UUID


@dataclass
class Document:
    """Represents a source document."""
    source_id: str
    content: str
    metadata: Dict[str, Any] | None = None


@dataclass
class Chunk:
    """Represents a text chunk from a document."""
    content: str
    content_hash: str
    document_id: UUID | None = None
    idx: int | None = None  # Index within document
    metadata: Dict[str, Any] | None = None


@dataclass
class RetrievedChunk:
    """A chunk retrieved from vector search with similarity score."""
    chunk: Chunk
    score: float
    source_id: str | None = None


@dataclass
class EmbeddingResult:
    """Result from embedding generation."""
    embeddings: List[List[float]]
    token_usage: int | None = None
    model: str | None = None


@dataclass
class GenerationResult:
    """Result from LLM generation."""
    text: str
    tokens_in: int | None = None
    tokens_out: int | None = None
    model: str | None = None
    metadata: Dict[str, Any] | None = None


@dataclass
class AnswerResult:
    """Final answer result from RAG pipeline."""
    answer: str
    sources: List[Dict[str, Any]]  # List of {source_id, score}
    metadata: Dict[str, Any] | None = None


@dataclass
class PromptParts:
    """Components of a prompt for LLM generation."""
    system_prompt: str
    user_prompt: str
    context: str
    prompt_version: str | None = None