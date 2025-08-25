"""Token-based text chunking implementation."""

import hashlib
from abc import ABC, abstractmethod
from typing import List, Protocol

from app.core.tokens import rough_token_count
from .models import Chunk


class Chunker(Protocol):
    """Protocol for text chunking implementations."""
    
    def chunk_text(self, text: str, document_id: str | None = None) -> List[Chunk]:
        """Chunk text into overlapping segments."""
        ...


class DefaultTokenChunker:
    """
    Default chunker using simple token approximation.
    
    TODO: Implement model-specific tokenizer when needed.
    Currently uses whitespace-based approximation.
    """
    
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        """
        Initialize chunker.
        
        Args:
            chunk_size: Target number of tokens per chunk
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
    
    def chunk_text(self, text: str, document_id: str | None = None) -> List[Chunk]:
        """
        Chunk text into overlapping segments.
        
        Args:
            text: Input text to chunk
            document_id: Optional document ID for metadata
            
        Returns:
            List of Chunk objects with content and metadata
        """
        if not text.strip():
            return []
        
        # Split into words for rough token approximation
        words = text.split()
        
        if len(words) <= self.chunk_size:
            # Text is smaller than chunk size, return as single chunk
            content_hash = self._hash_content(text)
            return [Chunk(
                content=text,
                content_hash=content_hash,
                idx=0,
                metadata={"word_count": len(words)}
            )]
        
        chunks = []
        start_idx = 0
        chunk_idx = 0
        
        while start_idx < len(words):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(words))
            
            # Extract words for this chunk
            chunk_words = words[start_idx:end_idx]
            chunk_content = " ".join(chunk_words)
            
            # Generate deterministic content hash
            content_hash = self._hash_content(chunk_content)
            
            chunk = Chunk(
                content=chunk_content,
                content_hash=content_hash,
                idx=chunk_idx,
                metadata={
                    "word_count": len(chunk_words),
                    "start_word_idx": start_idx,
                    "end_word_idx": end_idx,
                    "document_id": document_id,
                }
            )
            chunks.append(chunk)
            
            # Move start index for next chunk with overlap
            start_idx = end_idx - self.chunk_overlap
            chunk_idx += 1
            
            # Prevent infinite loop if overlap is too large
            if start_idx <= chunks[-1].metadata.get("start_word_idx", 0):
                start_idx = end_idx
        
        return chunks
    
    def _hash_content(self, content: str) -> str:
        """Generate deterministic hash for content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]