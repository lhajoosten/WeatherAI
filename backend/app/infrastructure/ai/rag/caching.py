"""Caching implementations for RAG pipeline."""

from abc import ABC, abstractmethod
from typing import Any, List
import json
import structlog

from app.core.redis_client import redis_client
from app.core.settings import get_settings
from app.core.hashing import sha256_text, hash_text_list, create_cache_key
from app.core.constants import CachePrefix, PROMPT_VERSION
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
    """Redis-based embedding cache implementation with Phase 4 enhancements."""
    
    def __init__(self, key_prefix: str = CachePrefix.EMBEDDING):
        """
        Initialize Redis embedding cache.
        
        Args:
            key_prefix: Prefix for cache keys
        """
        self.key_prefix = key_prefix
    
    def _create_cache_key(self, texts: List[str], model: str) -> str:
        """Create cache key with model hash as per Phase 4 requirements."""
        text_hash = hash_text_list(texts)
        return f"{self.key_prefix}:{model}:{text_hash}"
    
    async def get(self, texts: List[str], model: str = "text-embedding-ada-002") -> EmbeddingResult | None:
        """
        Get cached embeddings for texts.
        
        Args:
            texts: List of texts to get embeddings for
            model: Model name for cache key
            
        Returns:
            Cached EmbeddingResult or None if not found
        """
        if not texts:
            return None
        
        try:
            # Create cache key with model
            cache_key = self._create_cache_key(texts, model)
            
            # Get from Redis
            cached_data = await redis_client.get(cache_key)
            if not cached_data:
                logger.debug("Embedding cache miss", num_texts=len(texts), model=model)
                return None
            
            # Deserialize
            data = json.loads(cached_data)
            result = EmbeddingResult(
                embeddings=data["embeddings"],
                token_usage=data.get("token_usage"),
                model=data.get("model", model)
            )
            
            logger.debug(
                "Embedding cache hit",
                num_texts=len(texts),
                model=model,
                cache_key=cache_key[:16] + "..."
            )
            return result
            
        except Exception as e:
            logger.warning(
                "Embedding cache get failed",
                error=str(e),
                num_texts=len(texts),
                model=model
            )
            return None
    
    async def set(self, texts: List[str], result: EmbeddingResult, model: str = "text-embedding-ada-002", ttl: int = 604800) -> None:
        """
        Cache embeddings for texts with Phase 4 TTL (7 days default).
        
        Args:
            texts: List of texts
            result: Embedding result to cache
            model: Model name for cache key
            ttl: Time to live in seconds (default 7 days)
        """
        if not texts or not result.embeddings:
            return
        
        try:
            # Create cache key with model
            cache_key = self._create_cache_key(texts, model)
            
            # Serialize result
            data = {
                "embeddings": result.embeddings,
                "token_usage": result.token_usage,
                "model": result.model or model
            }
            
            # Store in Redis
            await redis_client.setex(cache_key, ttl, json.dumps(data))
            
            logger.debug(
                "Embedding cached",
                num_texts=len(texts),
                model=model,
                cache_key=cache_key[:16] + "...",
                ttl=ttl
            )
            
        except Exception as e:
            logger.warning(
                "Embedding cache set failed",
                error=str(e),
                num_texts=len(texts),
                model=model
            )


class RedisAnswerCache(AnswerCache):
    """Redis-based answer cache implementation with Phase 4 enhancements."""
    
    def __init__(self, key_prefix: str = CachePrefix.RAG_ANSWER):
        """
        Initialize Redis answer cache.
        
        Args:
            key_prefix: Prefix for cache keys
        """
        self.key_prefix = key_prefix
    
    def _create_cache_key(self, query: str, prompt_version: str) -> str:
        """Create cache key with prompt version as per Phase 4 requirements."""
        query_hash = sha256_text(query.strip().lower())
        return f"{self.key_prefix}:{query_hash}:{prompt_version}"
    
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
            # Create cache key with prompt version
            cache_key = self._create_cache_key(query, prompt_version)
            
            # Get from Redis
            cached_data = await redis_client.get(cache_key)
            if not cached_data:
                logger.debug("Answer cache miss", query_length=len(query), prompt_version=prompt_version)
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
                prompt_version=prompt_version,
                cache_key=cache_key[:16] + "..."
            )
            return result
            
        except Exception as e:
            logger.warning(
                "Answer cache get failed",
                error=str(e),
                query_length=len(query),
                prompt_version=prompt_version
            )
            return None
    
    async def set(
        self, 
        query: str, 
        prompt_version: str, 
        result: AnswerResult, 
        ttl: int = 3600  # Phase 4: 1 hour default instead of 6 hours
    ) -> None:
        """
        Cache answer for query with Phase 4 TTL (1 hour default).
        
        Args:
            query: User query
            prompt_version: Version of prompt template
            result: Answer result to cache
            ttl: Time to live in seconds (default 1 hour)
        """
        if not query.strip() or not result.answer:
            return
        
        try:
            # Create cache key with prompt version
            cache_key = self._create_cache_key(query, prompt_version)
            
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
                prompt_version=prompt_version,
                cache_key=cache_key[:16] + "...",
                ttl=ttl
            )
            
        except Exception as e:
            logger.warning(
                "Answer cache set failed",
                error=str(e),
                query_length=len(query),
                prompt_version=prompt_version
            )


# Factory functions for easy instantiation
def create_embedding_cache() -> EmbeddingCache:
    """Create embedding cache instance with default configuration."""
    return RedisEmbeddingCache()


def create_answer_cache() -> AnswerCache:
    """Create answer cache instance with default configuration."""
    settings = get_settings()
    return RedisAnswerCache()