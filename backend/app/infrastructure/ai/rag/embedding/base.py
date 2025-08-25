"""Abstract base classes for embedding implementations."""

from abc import ABC, abstractmethod
from typing import List

from ..models import EmbeddingResult


class Embedder(ABC):
    """Abstract base class for text embedding implementations."""
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            EmbeddingResult containing embeddings and metadata
        """
        pass
    
    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Get the dimensionality of embeddings produced by this embedder."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name/identifier of the embedding model."""
        pass