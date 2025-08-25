"""Tests for prompt versioning - Phase 4."""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch

from app.core.constants import PROMPT_VERSION
from app.schemas.rag_stream import StreamDoneEvent, StreamErrorEvent
from app.infrastructure.ai.rag.streaming_service import RAGStreamingService
from app.infrastructure.ai.rag.models import AnswerResult


class TestPromptVersioning:
    """Test prompt versioning in events and caching."""
    
    def test_prompt_version_constant(self):
        """Test that prompt version constant is properly defined."""
        assert PROMPT_VERSION == "v1"
    
    def test_done_event_includes_prompt_version(self):
        """Test that done events include prompt version."""
        
        event = StreamDoneEvent.create(
            total_tokens=50,
            sources_count=3
        )
        
        assert event.data["prompt_version"] == PROMPT_VERSION
    
    def test_done_event_with_custom_version(self):
        """Test done event with custom prompt version."""
        
        custom_version = "v2"
        event = StreamDoneEvent.create(
            total_tokens=50,
            sources_count=3,
            prompt_version=custom_version
        )
        
        assert event.data["prompt_version"] == custom_version
    
    def test_done_event_guardrail_includes_version(self):
        """Test that guardrail done events include prompt version."""
        
        event = StreamDoneEvent.create(
            sources_count=0,
            guardrail="no_context"
        )
        
        assert event.data["prompt_version"] == PROMPT_VERSION
        assert event.data["guardrail"] == "no_context"
    
    def test_error_event_includes_prompt_version(self):
        """Test that error events include prompt version."""
        
        event = StreamErrorEvent.create(
            error_code="validation_error",
            message="Test error"
        )
        
        assert event.data["prompt_version"] == PROMPT_VERSION
    
    def test_done_event_json_serialization(self):
        """Test that done event properly serializes prompt version."""
        
        event = StreamDoneEvent.create(
            total_tokens=100,
            sources_count=5
        )
        
        json_str = event.model_dump_json()
        parsed = json.loads(json_str)
        
        assert parsed["type"] == "done"
        assert parsed["data"]["prompt_version"] == PROMPT_VERSION
        assert parsed["data"]["total_tokens"] == 100
        assert parsed["data"]["sources_count"] == 5


class TestPromptVersionInStreaming:
    """Test prompt version integration in streaming responses."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.rag_max_query_length = 2000
        settings.rag_similarity_threshold = 0.55
        return settings
    
    @pytest.fixture
    def mock_pipeline(self):
        """Mock RAG pipeline."""
        pipeline = MagicMock()
        pipeline.answer_cache = AsyncMock()
        pipeline.retriever = AsyncMock()
        pipeline.prompt_builder = MagicMock()
        pipeline.llm_generator = AsyncMock()
        return pipeline
    
    @pytest.fixture
    def streaming_service(self, mock_pipeline, mock_settings):
        """Create streaming service with mocked dependencies."""
        with patch('app.infrastructure.ai.rag.streaming_service.get_settings', return_value=mock_settings):
            return RAGStreamingService(mock_pipeline)
    
    @pytest.mark.asyncio
    async def test_cache_hit_includes_prompt_version(self, streaming_service):
        """Test that cached responses include prompt version in done event."""
        
        # Mock cache hit
        cached_answer = AnswerResult(
            answer="Cached response for testing",
            sources=[{"source_id": "doc1", "score": 0.8}],
            metadata={"cached": True}
        )
        streaming_service.pipeline.answer_cache.get.return_value = cached_answer
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Find done event
        done_events = [e for e in events if '"type": "done"' in e]
        assert len(done_events) == 1
        
        done_event = done_events[0]
        assert f'"prompt_version": "{PROMPT_VERSION}"' in done_event
        assert '"cache_hit": true' in done_event
    
    @pytest.mark.asyncio
    async def test_guardrail_response_includes_prompt_version(self, streaming_service):
        """Test that guardrail responses include prompt version."""
        
        # Mock no cache hit
        streaming_service.pipeline.answer_cache.get.return_value = None
        
        # Mock empty retrieval results to trigger guardrail
        streaming_service.pipeline.retriever.retrieve.return_value = []
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Should contain error event with prompt version
        error_events = [e for e in events if '"type": "error"' in e]
        assert len(error_events) > 0
        
        error_event = error_events[0]
        assert f'"prompt_version": "{PROMPT_VERSION}"' in error_event
    
    @pytest.mark.asyncio
    async def test_successful_response_includes_prompt_version(self, streaming_service):
        """Test that successful responses include prompt version."""
        
        # Mock no cache hit
        streaming_service.pipeline.answer_cache.get.return_value = None
        
        # Mock successful retrieval
        from app.infrastructure.ai.rag.models import RetrievedChunk, DocumentChunk
        
        chunks = [
            RetrievedChunk(
                chunk=DocumentChunk(
                    content="High quality content",
                    document_id="doc1",
                    chunk_index=0,
                    metadata={}
                ),
                score=0.8,
                source_id="source1"
            )
        ]
        streaming_service.pipeline.retriever.retrieve.return_value = chunks
        
        # Mock prompt builder
        streaming_service.pipeline.prompt_builder.build_prompt.return_value = MagicMock()
        streaming_service.pipeline.prompt_builder.estimate_token_count.return_value = 100
        
        # Mock LLM streaming
        async def mock_stream_llm(prompt_parts, context_metadata):
            yield "Generated"
            yield " response"
        
        streaming_service._stream_llm_response = mock_stream_llm
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Find done event
        done_events = [e for e in events if '"type": "done"' in e]
        assert len(done_events) == 1
        
        done_event = done_events[0]
        assert f'"prompt_version": "{PROMPT_VERSION}"' in done_event
        # Should not have cache_hit since this was generated
        assert '"cache_hit"' not in done_event or '"cache_hit": false' in done_event


class TestPromptVersionInCaching:
    """Test prompt version integration with caching."""
    
    @pytest.mark.asyncio
    async def test_answer_cache_key_includes_prompt_version(self):
        """Test that answer cache keys include prompt version."""
        
        from app.infrastructure.ai.rag.caching import RedisAnswerCache
        
        cache = RedisAnswerCache()
        query = "test query"
        
        # Test key generation with current prompt version
        key = cache._create_cache_key(query, PROMPT_VERSION)
        
        assert PROMPT_VERSION in key
        assert query.lower().replace(" ", "") not in key  # Should be hashed
    
    @pytest.mark.asyncio
    async def test_different_prompt_versions_different_keys(self):
        """Test that different prompt versions generate different cache keys."""
        
        from app.infrastructure.ai.rag.caching import RedisAnswerCache
        
        cache = RedisAnswerCache()
        query = "same query"
        
        key_v1 = cache._create_cache_key(query, "v1")
        key_v2 = cache._create_cache_key(query, "v2")
        
        assert key_v1 != key_v2
        assert "v1" in key_v1
        assert "v2" in key_v2
    
    @pytest.mark.asyncio
    async def test_cache_get_with_prompt_version(self):
        """Test cache retrieval with prompt version."""
        
        from app.infrastructure.ai.rag.caching import RedisAnswerCache
        from app.infrastructure.ai.rag.models import AnswerResult
        
        cache = RedisAnswerCache()
        
        with patch('app.infrastructure.ai.rag.caching.redis_client') as mock_redis:
            # Mock cache hit
            cached_data = {
                "answer": "Test answer",
                "sources": [],
                "metadata": {"version": "v1"}
            }
            mock_redis.get.return_value = json.dumps(cached_data)
            
            result = await cache.get("test query", PROMPT_VERSION)
            
            assert result is not None
            assert result.answer == "Test answer"
            
            # Verify cache key included prompt version
            call_args = mock_redis.get.call_args[0]
            cache_key = call_args[0]
            assert PROMPT_VERSION in cache_key


class TestPromptVersionInMetrics:
    """Test prompt version inclusion in metrics and logging."""
    
    @pytest.mark.asyncio
    async def test_error_logging_includes_prompt_version(self):
        """Test that error logging includes prompt version."""
        
        from app.infrastructure.ai.rag.metrics import record_pipeline_error
        
        with patch('app.infrastructure.ai.rag.metrics.logger') as mock_logger:
            record_pipeline_error("TestError", "streaming", "test query")
            
            # Verify error logging was called with prompt version
            mock_logger.error.assert_called_once()
            call_kwargs = mock_logger.error.call_args[1]
            assert call_kwargs["prompt_version"] == PROMPT_VERSION
    
    @pytest.mark.asyncio
    async def test_pipeline_metrics_include_prompt_version(self):
        """Test that pipeline metrics include prompt version."""
        
        from app.infrastructure.ai.rag.metrics import log_pipeline_metrics
        
        with patch('app.infrastructure.ai.rag.metrics.logger') as mock_logger:
            log_pipeline_metrics(
                query="test query",
                num_retrieved=3,
                num_filtered=3,
                min_similarity=0.7,
                context_tokens=100,
                cache_hits={"answer": False, "embedding": False}
            )
            
            # Verify metrics logging includes prompt version
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs["prompt_version"] == PROMPT_VERSION


if __name__ == "__main__":
    pytest.main([__file__])