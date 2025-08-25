"""Tests for enhanced caching with Phase 4 features."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.ai.rag.caching import (
    RedisEmbeddingCache,
    RedisAnswerCache,
    create_embedding_cache,
    create_answer_cache
)
from app.infrastructure.ai.rag.models import EmbeddingResult, AnswerResult
from app.core.constants import CachePrefix, PROMPT_VERSION


class TestEmbeddingCacheEnhancements:
    """Test embedding cache with Phase 4 enhancements."""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        return AsyncMock()
    
    @pytest.fixture
    def embedding_cache(self):
        """Create embedding cache instance."""
        return RedisEmbeddingCache()
    
    @pytest.fixture
    def sample_embedding_result(self):
        """Sample embedding result."""
        return EmbeddingResult(
            embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            token_usage=20,
            model="text-embedding-ada-002"
        )
    
    def test_cache_key_with_model_hash(self, embedding_cache):
        """Test cache key generation includes model hash."""
        texts = ["test text 1", "test text 2"]
        model = "text-embedding-ada-002"
        
        cache_key = embedding_cache._create_cache_key(texts, model)
        
        # Should include prefix, model, and text hash
        assert cache_key.startswith(f"{CachePrefix.EMBEDDING}:")
        assert model in cache_key
        assert len(cache_key.split(":")) == 3  # prefix:model:hash
    
    def test_cache_key_consistency(self, embedding_cache):
        """Test cache key consistency for same inputs."""
        texts = ["hello", "world"]
        model = "test-model"
        
        key1 = embedding_cache._create_cache_key(texts, model)
        key2 = embedding_cache._create_cache_key(texts, model)
        
        assert key1 == key2
    
    def test_cache_key_different_models(self, embedding_cache):
        """Test different models produce different cache keys."""
        texts = ["same text"]
        
        key1 = embedding_cache._create_cache_key(texts, "model-1")
        key2 = embedding_cache._create_cache_key(texts, "model-2")
        
        assert key1 != key2
    
    @pytest.mark.asyncio
    async def test_get_with_model_parameter(self, embedding_cache, sample_embedding_result, mock_redis_client):
        """Test cache get with model parameter."""
        
        with patch('app.infrastructure.ai.rag.caching.redis_client', mock_redis_client):
            # Mock cache hit
            cached_data = {
                "embeddings": sample_embedding_result.embeddings,
                "token_usage": sample_embedding_result.token_usage,
                "model": sample_embedding_result.model
            }
            mock_redis_client.get.return_value = json.dumps(cached_data)
            
            result = await embedding_cache.get(["test"], model="text-embedding-ada-002")
            
            assert result is not None
            assert result.embeddings == sample_embedding_result.embeddings
            assert result.model == "text-embedding-ada-002"
            
            # Verify correct cache key was used
            call_args = mock_redis_client.get.call_args[0]
            cache_key = call_args[0]
            assert "text-embedding-ada-002" in cache_key
    
    @pytest.mark.asyncio
    async def test_set_with_7day_ttl(self, embedding_cache, sample_embedding_result, mock_redis_client):
        """Test cache set with 7-day TTL (Phase 4 default)."""
        
        with patch('app.infrastructure.ai.rag.caching.redis_client', mock_redis_client):
            await embedding_cache.set(
                ["test text"],
                sample_embedding_result,
                model="text-embedding-ada-002"
            )
            
            # Verify setex was called with 7-day TTL
            mock_redis_client.setex.assert_called_once()
            call_args = mock_redis_client.setex.call_args
            
            cache_key, ttl, data = call_args[0]
            assert ttl == 604800  # 7 days in seconds
            assert "text-embedding-ada-002" in cache_key
    
    @pytest.mark.asyncio
    async def test_cache_miss_with_model(self, embedding_cache, mock_redis_client):
        """Test cache miss handling with model parameter."""
        
        with patch('app.infrastructure.ai.rag.caching.redis_client', mock_redis_client):
            mock_redis_client.get.return_value = None
            
            result = await embedding_cache.get(["test"], model="test-model")
            
            assert result is None


class TestAnswerCacheEnhancements:
    """Test answer cache with Phase 4 enhancements."""
    
    @pytest.fixture
    def answer_cache(self):
        """Create answer cache instance."""
        return RedisAnswerCache()
    
    @pytest.fixture
    def sample_answer_result(self):
        """Sample answer result."""
        return AnswerResult(
            answer="This is a test answer",
            sources=[
                {"source_id": "doc1", "score": 0.8},
                {"source_id": "doc2", "score": 0.7}
            ],
            metadata={"tokens": 50}
        )
    
    def test_cache_key_with_prompt_version(self, answer_cache):
        """Test cache key includes prompt version."""
        query = "test query"
        prompt_version = "v1"
        
        cache_key = answer_cache._create_cache_key(query, prompt_version)
        
        # Should include prefix, query hash, and prompt version
        assert cache_key.startswith(f"{CachePrefix.RAG_ANSWER}:")
        assert prompt_version in cache_key
        assert len(cache_key.split(":")) == 3  # prefix:query_hash:version
    
    def test_cache_key_different_versions(self, answer_cache):
        """Test different prompt versions produce different keys."""
        query = "same query"
        
        key_v1 = answer_cache._create_cache_key(query, "v1")
        key_v2 = answer_cache._create_cache_key(query, "v2")
        
        assert key_v1 != key_v2
    
    def test_cache_key_query_normalization(self, answer_cache):
        """Test query normalization in cache key generation."""
        prompt_version = "v1"
        
        # Different formats of same query should produce same key
        key1 = answer_cache._create_cache_key("Test Query", prompt_version)
        key2 = answer_cache._create_cache_key("test query", prompt_version)
        key3 = answer_cache._create_cache_key("  TEST QUERY  ", prompt_version)
        
        assert key1 == key2 == key3
    
    @pytest.mark.asyncio
    async def test_get_with_prompt_version(self, answer_cache, sample_answer_result):
        """Test cache get with prompt version."""
        
        with patch('app.infrastructure.ai.rag.caching.redis_client') as mock_redis:
            # Mock cache hit
            cached_data = {
                "answer": sample_answer_result.answer,
                "sources": sample_answer_result.sources,
                "metadata": sample_answer_result.metadata
            }
            mock_redis.get.return_value = json.dumps(cached_data)
            
            result = await answer_cache.get("test query", PROMPT_VERSION)
            
            assert result is not None
            assert result.answer == sample_answer_result.answer
            
            # Verify cache key includes prompt version
            call_args = mock_redis.get.call_args[0]
            cache_key = call_args[0]
            assert PROMPT_VERSION in cache_key
    
    @pytest.mark.asyncio
    async def test_set_with_1hour_ttl(self, answer_cache, sample_answer_result):
        """Test cache set with 1-hour TTL (Phase 4 default)."""
        
        with patch('app.infrastructure.ai.rag.caching.redis_client') as mock_redis:
            await answer_cache.set(
                "test query",
                PROMPT_VERSION,
                sample_answer_result
            )
            
            # Verify setex was called with 1-hour TTL
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            
            cache_key, ttl, data = call_args[0]
            assert ttl == 3600  # 1 hour in seconds
            assert PROMPT_VERSION in cache_key
    
    @pytest.mark.asyncio
    async def test_custom_ttl_override(self, answer_cache, sample_answer_result):
        """Test custom TTL override."""
        
        with patch('app.infrastructure.ai.rag.caching.redis_client') as mock_redis:
            custom_ttl = 7200  # 2 hours
            
            await answer_cache.set(
                "test query",
                PROMPT_VERSION,
                sample_answer_result,
                ttl=custom_ttl
            )
            
            # Verify custom TTL was used
            call_args = mock_redis.setex.call_args
            cache_key, ttl, data = call_args[0]
            assert ttl == custom_ttl


class TestCacheFactoryFunctions:
    """Test cache factory functions."""
    
    def test_create_embedding_cache(self):
        """Test embedding cache factory."""
        cache = create_embedding_cache()
        
        assert isinstance(cache, RedisEmbeddingCache)
        assert cache.key_prefix == CachePrefix.EMBEDDING
    
    def test_create_answer_cache(self):
        """Test answer cache factory."""
        cache = create_answer_cache()
        
        assert isinstance(cache, RedisAnswerCache)
        assert cache.key_prefix == CachePrefix.RAG_ANSWER


class TestCacheIntegration:
    """Test cache integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_embedding_cache_model_isolation(self):
        """Test that different models don't interfere with each other."""
        cache = RedisEmbeddingCache()
        
        with patch('app.infrastructure.ai.rag.caching.redis_client') as mock_redis:
            # Simulate different models returning different data
            def get_side_effect(key):
                if "model-a" in key:
                    return json.dumps({
                        "embeddings": [[1, 2, 3]],
                        "token_usage": 10,
                        "model": "model-a"
                    })
                elif "model-b" in key:
                    return json.dumps({
                        "embeddings": [[4, 5, 6]],
                        "token_usage": 15,
                        "model": "model-b"
                    })
                return None
            
            mock_redis.get.side_effect = get_side_effect
            
            # Get from different models
            result_a = await cache.get(["test"], model="model-a")
            result_b = await cache.get(["test"], model="model-b")
            
            assert result_a.embeddings == [[1, 2, 3]]
            assert result_b.embeddings == [[4, 5, 6]]
            assert result_a.model == "model-a"
            assert result_b.model == "model-b"
    
    @pytest.mark.asyncio
    async def test_answer_cache_version_isolation(self):
        """Test that different prompt versions don't interfere."""
        cache = RedisAnswerCache()
        
        with patch('app.infrastructure.ai.rag.caching.redis_client') as mock_redis:
            # Simulate different versions returning different data
            def get_side_effect(key):
                if ":v1" in key:
                    return json.dumps({
                        "answer": "Answer from v1",
                        "sources": [],
                        "metadata": {"version": "v1"}
                    })
                elif ":v2" in key:
                    return json.dumps({
                        "answer": "Answer from v2",
                        "sources": [],
                        "metadata": {"version": "v2"}
                    })
                return None
            
            mock_redis.get.side_effect = get_side_effect
            
            # Get from different versions
            result_v1 = await cache.get("test query", "v1")
            result_v2 = await cache.get("test query", "v2")
            
            assert result_v1.answer == "Answer from v1"
            assert result_v2.answer == "Answer from v2"
            assert result_v1.metadata["version"] == "v1"
            assert result_v2.metadata["version"] == "v2"


if __name__ == "__main__":
    pytest.main([__file__])