"""Abstract base classes for vector storage implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from uuid import UUID

from ..models import Chunk, RetrievedChunk


class VectorStore(ABC):
    """Abstract base class for vector storage implementations."""
    
    @abstractmethod
    async def add(
        self, 
        chunks: List[Chunk], 
        embeddings: List[List[float]], 
        metadata: Dict[str, Any] | None = None
    ) -> None:
        """
        Add chunks with their embeddings to the vector store.
        
        Args:
            chunks: List of text chunks to store
            embeddings: Corresponding embeddings for each chunk
            metadata: Optional metadata to associate with the chunks
        """
        pass
    
    @abstractmethod
    async def query(
        self, 
        query_embedding: List[float], 
        top_k: int = 10,
        filter_metadata: Dict[str, Any] | None = None
    ) -> List[RetrievedChunk]:
        """
        Query the vector store for similar chunks.
        
        Args:
            query_embedding: Embedding vector for the query
            top_k: Maximum number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of retrieved chunks with similarity scores
        """
        pass
    
    @abstractmethod
    async def delete(self, chunk_ids: List[str]) -> None:
        """
        Delete chunks from the vector store.
        
        Args:
            chunk_ids: List of chunk IDs to delete
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all chunks from the vector store."""
        pass