"""Caching implementations for RAG pipeline."""

from abc import ABC, abstractmethod
from typing import Any, List
import json
import structlog

from app.core.redis_client import redis_client
from app.core.config import get_settings
from app.utils.hashing import sha256_text, hash_text_list, create_cache_key
from .models import EmbeddingResult, AnswerResult

logger = structlog.get_logger(__name__)


class EmbeddingCache(ABC):
    """Abstract interface for embedding caching."""
    
    @abstractmethod
    async def get(self, texts: List[str]) -> EmbeddingResult | None:
        """Get cached embeddings for texts."""
        pass
    
    @abstractmethod
    async def set(self, texts: List[str], result: EmbeddingResult, ttl: int = 3600) -> None:
        """Cache embeddings for texts."""
        pass


class AnswerCache(ABC):
    """Abstract interface for answer caching."""
    
    @abstractmethod
    async def get(self, query: str, prompt_version: str) -> AnswerResult | None:
        """Get cached answer for query."""
        pass
    
    @abstractmethod
    async def set(
        self, 
        query: str, 
        prompt_version: str, 
        result: AnswerResult, 
        ttl: int = 21600
    ) -> None:
        """Cache answer for query."""
        pass


class RedisEmbeddingCache(EmbeddingCache):
    """Redis-based embedding cache implementation."""
    
    def __init__(self, key_prefix: str = "rag:embed"):
        """
        Initialize Redis embedding cache.
        
        Args:
            key_prefix: Prefix for cache keys
        """
        self.key_prefix = key_prefix
    
    async def get(self, texts: List[str]) -> EmbeddingResult | None:
        """
        Get cached embeddings for texts.
        
        Args:
            texts: List of texts to get embeddings for
            
        Returns:
            Cached EmbeddingResult or None if not found
        """
        if not texts:
            return None
        
        try:
            # Create consistent cache key
            cache_key = create_cache_key(
                hash_text_list(texts),
                prefix=self.key_prefix
            )
            
            # Get from Redis
            cached_data = await redis_client.get(cache_key)
            if not cached_data:
                logger.debug("Embedding cache miss", num_texts=len(texts))
                return None
            
            # Deserialize
            data = json.loads(cached_data)
            result = EmbeddingResult(
                embeddings=data["embeddings"],
                token_usage=data.get("token_usage"),
                model=data.get("model")
            )
            
            logger.debug(
                "Embedding cache hit",
                num_texts=len(texts),
                cache_key=cache_key[:16] + "..."
            )
            return result
            
        except Exception as e:
            logger.warning(
                "Embedding cache get failed",
                error=str(e),
                num_texts=len(texts)
            )
            return None
    
    async def set(self, texts: List[str], result: EmbeddingResult, ttl: int = 3600) -> None:
        """
        Cache embeddings for texts.
        
        Args:
            texts: List of texts
            result: Embedding result to cache
            ttl: Time to live in seconds
        """
        if not texts or not result.embeddings:
            return
        
        try:
            # Create consistent cache key
            cache_key = create_cache_key(
                hash_text_list(texts),
                prefix=self.key_prefix
            )
            
            # Serialize result
            data = {
                "embeddings": result.embeddings,
                "token_usage": result.token_usage,
                "model": result.model
            }
            
            # Store in Redis
            await redis_client.setex(cache_key, ttl, json.dumps(data))
            
            logger.debug(
                "Embedding cached",
                num_texts=len(texts),
                cache_key=cache_key[:16] + "...",
                ttl=ttl
            )
            
        except Exception as e:
            logger.warning(
                "Embedding cache set failed",
                error=str(e),
                num_texts=len(texts)
            )


class RedisAnswerCache(AnswerCache):
    """Redis-based answer cache implementation."""
    
    def __init__(self, key_prefix: str = "rag:answer"):
        """
        Initialize Redis answer cache.
        
        Args:
            key_prefix: Prefix for cache keys
        """
        self.key_prefix = key_prefix
    
    async def get(self, query: str, prompt_version: str) -> AnswerResult | None:
        """
        Get cached answer for query.
        
        Args:
            query: User query
            prompt_version: Version of prompt template used
            
        Returns:
            Cached AnswerResult or None if not found
        """
        if not query.strip():
            return None
        
        try:
            # Normalize query for consistent caching
            normalized_query = query.strip().lower()
            
            # Create cache key
            cache_key = create_cache_key(
                sha256_text(normalized_query),
                prompt_version,
                prefix=self.key_prefix
            )
            
            # Get from Redis
            cached_data = await redis_client.get(cache_key)
            if not cached_data:
                logger.debug("Answer cache miss", query_length=len(query))
                return None
            
            # Deserialize
            data = json.loads(cached_data)
            result = AnswerResult(
                answer=data["answer"],
                sources=data["sources"],
                metadata=data.get("metadata", {})
            )
            
            logger.debug(
                "Answer cache hit",
                query_length=len(query),
                cache_key=cache_key[:16] + "..."
            )
            return result
            
        except Exception as e:
            logger.warning(
                "Answer cache get failed",
                error=str(e),
                query_length=len(query)
            )
            return None
    
    async def set(
        self, 
        query: str, 
        prompt_version: str, 
        result: AnswerResult, 
        ttl: int = 21600
    ) -> None:
        """
        Cache answer for query.
        
        Args:
            query: User query
            prompt_version: Version of prompt template
            result: Answer result to cache
            ttl: Time to live in seconds (default 6 hours)
        """
        if not query.strip() or not result.answer:
            return
        
        try:
            # Normalize query for consistent caching
            normalized_query = query.strip().lower()
            
            # Create cache key
            cache_key = create_cache_key(
                sha256_text(normalized_query),
                prompt_version,
                prefix=self.key_prefix
            )
            
            # Serialize result
            data = {
                "answer": result.answer,
                "sources": result.sources,
                "metadata": result.metadata or {}
            }
            
            # Store in Redis
            await redis_client.setex(cache_key, ttl, json.dumps(data))
            
            logger.debug(
                "Answer cached",
                query_length=len(query),
                cache_key=cache_key[:16] + "...",
                ttl=ttl
            )
            
        except Exception as e:
            logger.warning(
                "Answer cache set failed",
                error=str(e),
                query_length=len(query)
            )


# Factory functions for easy instantiation
def create_embedding_cache() -> EmbeddingCache:
    """Create embedding cache instance with default configuration."""
    return RedisEmbeddingCache()


def create_answer_cache() -> AnswerCache:
    """Create answer cache instance with default configuration."""
    settings = get_settings()
    return RedisAnswerCache()