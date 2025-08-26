"""Azure OpenAI embedding implementation."""

import asyncio
from typing import List

from openai import AsyncAzureOpenAI

from app.core.settings import get_settings
from app.core.hashing import hash_text_list
from ..models import EmbeddingResult
from .base import Embedder


class AzureOpenAIEmbedder(Embedder):
    """Azure OpenAI embedding implementation with batching and caching."""
    
    def __init__(self, cache=None):
        """
        Initialize Azure OpenAI embedder.
        
        Args:
            cache: Optional cache implementation for embeddings
        """
        self.settings = get_settings()
        self.cache = cache
        
        # Initialize Azure OpenAI client
        if not self.settings.azure_openai_endpoint or not self.settings.azure_openai_api_key:
            raise ValueError("Azure OpenAI endpoint and API key must be configured")
        
        self.client = AsyncAzureOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=self.settings.azure_openai_api_key,
            api_version="2024-02-01",  # Use stable API version
        )
    
    async def embed_texts(self, texts: List[str]) -> EmbeddingResult:
        """
        Generate embeddings for texts with caching support.
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            EmbeddingResult with embeddings and metadata
        """
        if not texts:
            return EmbeddingResult(embeddings=[], token_usage=0, model=self.model_name)
        
        # Check cache if available
        if self.cache:
            cache_key = hash_text_list(texts)
            cached_result = await self.cache.get("embedding", cache_key)
            if cached_result:
                return cached_result
        
        # Batch texts for API efficiency (Azure OpenAI supports up to 16 texts per request)
        batch_size = 16
        all_embeddings = []
        total_tokens = 0
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_result = await self._embed_batch(batch)
            
            all_embeddings.extend(batch_result.embeddings)
            total_tokens += batch_result.token_usage or 0
        
        result = EmbeddingResult(
            embeddings=all_embeddings,
            token_usage=total_tokens,
            model=self.model_name
        )
        
        # Cache result if cache is available
        if self.cache:
            await self.cache.set("embedding", cache_key, result, ttl=3600)  # 1 hour cache
        
        return result
    
    async def _embed_batch(self, texts: List[str]) -> EmbeddingResult:
        """
        Embed a single batch of texts.
        
        Args:
            texts: Batch of texts to embed (max 16)
            
        Returns:
            EmbeddingResult for this batch
        """
        if not self.settings.azure_openai_embedding_deployment:
            raise ValueError("Azure OpenAI embedding deployment must be configured")
        
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=self.settings.azure_openai_embedding_deployment,
            )
            
            embeddings = [item.embedding for item in response.data]
            
            # TODO: Gather token usage if returned by API
            # Azure OpenAI may not always return usage info for embeddings
            token_usage = getattr(response, 'usage', None)
            token_count = token_usage.total_tokens if token_usage else None
            
            return EmbeddingResult(
                embeddings=embeddings,
                token_usage=token_count,
                model=self.model_name
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension from settings."""
        return self.settings.azure_openai_embedding_dim
    
    @property
    def model_name(self) -> str:
        """Get embedding model deployment name."""
        return self.settings.azure_openai_embedding_deployment or "azure-embedding"