"""Tests for RAG guardrails - Phase 4."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.infrastructure.ai.rag.streaming_service import RAGStreamingService
from app.infrastructure.ai.rag.models import RetrievedChunk, Chunk, AnswerResult
from app.domain.exceptions import NoContextAvailableError, QueryValidationError
from app.core.constants import DomainErrorCode


class TestSimilarityThresholdGuardrail:
    """Test similarity threshold guardrail functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with Phase 4 defaults."""
        settings = MagicMock()
        settings.rag_max_query_length = 2000
        settings.rag_similarity_threshold = 0.55  # Phase 4 default
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
    
    def create_chunks_with_similarity(self, similarities):
        """Create retrieved chunks with specified similarity scores."""
        chunks = []
        for i, score in enumerate(similarities):
            chunk = RetrievedChunk(
                chunk=Chunk(
                    content=f"Content {i}",
                    content_hash=f"hash_{i}",
                    idx=i,
                    metadata={}
                ),
                score=score,
                source_id=f"source_{i}"
            )
            chunks.append(chunk)
        return chunks
    
    @pytest.mark.asyncio
    async def test_guardrail_triggers_low_average_similarity(self, streaming_service):
        """Test guardrail triggers when average similarity is below threshold."""
        
        # Mock no cache hit
        streaming_service.pipeline.answer_cache.get.return_value = None
        
        # Mock chunks with low average similarity
        # Similarities: [0.6, 0.5, 0.4] -> Average = 0.5 < 0.55
        low_sim_chunks = self.create_chunks_with_similarity([0.6, 0.5, 0.4])
        streaming_service.pipeline.retriever.retrieve.return_value = low_sim_chunks
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Should contain tokens for fallback response and done event with guardrail
        assert len(events) > 0
        
        # Last event should be done with guardrail trigger
        last_event = events[-1]
        assert "done" in last_event
        assert "guardrail" in last_event
        assert "no_context" in last_event
    
    @pytest.mark.asyncio
    async def test_guardrail_passes_high_average_similarity(self, streaming_service):
        """Test guardrail passes when average similarity is above threshold."""
        
        # Mock no cache hit
        streaming_service.pipeline.answer_cache.get.return_value = None
        
        # Mock chunks with high average similarity
        # Similarities: [0.8, 0.7, 0.6] -> Average = 0.7 > 0.55
        high_sim_chunks = self.create_chunks_with_similarity([0.8, 0.7, 0.6])
        streaming_service.pipeline.retriever.retrieve.return_value = high_sim_chunks
        
        # Mock prompt builder and LLM generator
        streaming_service.pipeline.prompt_builder.build_prompt.return_value = MagicMock()
        streaming_service.pipeline.prompt_builder.estimate_token_count.return_value = 100
        
        # Mock LLM generation for streaming
        async def mock_stream_llm(prompt_parts, context_metadata):
            yield "Test"
            yield " response"
        
        streaming_service._stream_llm_response = mock_stream_llm
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Should contain token events and done event without guardrail
        assert len(events) > 0
        
        # Should have token events
        token_events = [e for e in events if '"type": "token"' in e]
        assert len(token_events) > 0
        
        # Last event should be done without guardrail
        last_event = events[-1]
        assert "done" in last_event
        assert "guardrail" not in last_event or "no_context" not in last_event
    
    @pytest.mark.asyncio
    async def test_guardrail_boundary_case(self, streaming_service):
        """Test guardrail behavior exactly at threshold."""
        
        # Mock no cache hit
        streaming_service.pipeline.answer_cache.get.return_value = None
        
        # Mock chunks with average similarity exactly at threshold
        # Similarities: [0.55, 0.55, 0.55] -> Average = 0.55 = 0.55 (should pass)
        boundary_chunks = self.create_chunks_with_similarity([0.55, 0.55, 0.55])
        streaming_service.pipeline.retriever.retrieve.return_value = boundary_chunks
        
        # Mock prompt builder and LLM generator
        streaming_service.pipeline.prompt_builder.build_prompt.return_value = MagicMock()
        streaming_service.pipeline.prompt_builder.estimate_token_count.return_value = 100
        
        async def mock_stream_llm(prompt_parts, context_metadata):
            yield "Boundary"
            yield " test"
        
        streaming_service._stream_llm_response = mock_stream_llm
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Should pass guardrail (average >= threshold)
        last_event = events[-1]
        assert "done" in last_event
        # Should not trigger guardrail since 0.55 >= 0.55
    
    @pytest.mark.asyncio
    async def test_no_chunks_retrieved(self, streaming_service):
        """Test behavior when no chunks are retrieved."""
        
        # Mock no cache hit
        streaming_service.pipeline.answer_cache.get.return_value = None
        
        # Mock no chunks retrieved
        streaming_service.pipeline.retriever.retrieve.return_value = []
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            # Should raise NoContextAvailableError internally and convert to error event
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Should contain error event
        assert len(events) > 0
        error_events = [e for e in events if '"type": "error"' in e]
        assert len(error_events) > 0


class TestInputValidationGuardrails:
    """Test input validation guardrails."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with Phase 4 limits."""
        settings = MagicMock()
        settings.rag_max_query_length = 2000
        settings.rag_similarity_threshold = 0.55
        return settings
    
    @pytest.fixture
    def streaming_service(self, mock_settings):
        """Create streaming service for validation testing."""
        pipeline = MagicMock()
        with patch('app.infrastructure.ai.rag.streaming_service.get_settings', return_value=mock_settings):
            return RAGStreamingService(pipeline)
    
    def test_validate_empty_query(self, streaming_service):
        """Test validation of empty queries."""
        
        with pytest.raises(QueryValidationError, match="Query cannot be empty"):
            streaming_service._validate_query("")
        
        with pytest.raises(QueryValidationError, match="Query cannot be empty"):
            streaming_service._validate_query("   ")
    
    def test_validate_query_too_long(self, streaming_service):
        """Test validation of queries exceeding length limit."""
        
        long_query = "x" * 2001  # Exceeds 2000 char limit
        
        with pytest.raises(QueryValidationError, match="Query length exceeds maximum"):
            streaming_service._validate_query(long_query)
    
    def test_validate_query_at_limit(self, streaming_service):
        """Test validation of query exactly at limit."""
        
        query_at_limit = "x" * 2000  # Exactly at limit
        
        # Should not raise exception
        streaming_service._validate_query(query_at_limit)
    
    def test_validate_normal_query(self, streaming_service):
        """Test validation of normal query."""
        
        normal_query = "What is the weather like today?"
        
        # Should not raise exception
        streaming_service._validate_query(normal_query)
    
    @pytest.mark.asyncio
    async def test_validation_error_in_stream(self, streaming_service):
        """Test that validation errors are properly converted to error events."""
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer(""):  # Empty query
                events.append(event)
        
        # Should contain error event for validation failure
        assert len(events) == 1
        error_event = events[0]
        assert '"type": "error"' in error_event
        assert '"error_code": "validation_error"' in error_event


class TestCacheHitGuardrail:
    """Test cache hit behavior as a guardrail against unnecessary processing."""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Mock pipeline with cache."""
        pipeline = MagicMock()
        pipeline.answer_cache = AsyncMock()
        return pipeline
    
    @pytest.fixture
    def streaming_service(self, mock_pipeline):
        """Create streaming service with mocked pipeline."""
        settings = MagicMock()
        settings.rag_max_query_length = 2000
        settings.rag_similarity_threshold = 0.55
        
        with patch('app.infrastructure.ai.rag.streaming_service.get_settings', return_value=settings):
            return RAGStreamingService(mock_pipeline)
    
    @pytest.mark.asyncio
    async def test_cache_hit_bypasses_retrieval(self, streaming_service):
        """Test that cache hit bypasses retrieval and guardrails."""
        
        # Mock cache hit
        cached_answer = AnswerResult(
            answer="Cached response",
            sources=[{"source_id": "cached_doc", "score": 0.9}],
            metadata={"cached": True}
        )
        streaming_service.pipeline.answer_cache.get.return_value = cached_answer
        
        # Mock rate limiting to pass
        with patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
            events = []
            async for event in streaming_service.stream_answer("test query"):
                events.append(event)
        
        # Should stream cached answer and include cache_hit in done event
        assert len(events) > 0
        
        # Should have token events for cached content
        token_events = [e for e in events if '"type": "token"' in e]
        assert len(token_events) > 0
        
        # Last event should be done with cache_hit flag
        last_event = events[-1]
        assert '"type": "done"' in last_event
        assert '"cache_hit": true' in last_event
        
        # Retriever should not have been called
        streaming_service.pipeline.retriever.retrieve.assert_not_called()


class TestGuardrailMetrics:
    """Test that guardrails trigger proper metrics recording."""
    
    @pytest.mark.asyncio
    async def test_guardrail_metrics_recorded(self):
        """Test that guardrail triggers are recorded in metrics."""
        with patch('app.infrastructure.ai.rag.streaming_service.record_guardrail_trigger') as mock_record:
            # Create streaming service with low similarity chunks
            pipeline = MagicMock()
            pipeline.answer_cache.get.return_value = None

            # Mock chunks with low average similarity
            low_sim_chunks = [
                RetrievedChunk(
                    chunk=Chunk(content="test", content_hash="hash_test", idx=0, metadata={}),
                    score=0.4,
                    source_id="source1"
                )
            ]
            pipeline.retriever.retrieve.return_value = low_sim_chunks

            settings = MagicMock()
            settings.rag_max_query_length = 2000
            settings.rag_similarity_threshold = 0.55

            with patch('app.infrastructure.ai.rag.streaming_service.get_settings', return_value=settings), \
                 patch('app.infrastructure.ai.rag.streaming_service.check_streaming_rate_limit'):
                service = RAGStreamingService(pipeline)

                events = []
                async for event in service.stream_answer("test query"):
                    events.append(event)

                # Verify guardrail metric was recorded
                mock_record.assert_called_once()
                assert mock_record.call_args[0][0] == "similarity_threshold"
                assert mock_record.call_args[0][1] is True


if __name__ == "__main__":
    pytest.main([__file__])