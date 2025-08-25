"""Tests for RAG streaming endpoint - Phase 4."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.routes.rag import router
from app.infrastructure.ai.rag.pipeline import RAGPipeline
from app.infrastructure.ai.rag.streaming_service import RAGStreamingService
from app.schemas.rag_stream import StreamTokenEvent, StreamDoneEvent, StreamErrorEvent
from app.core.constants import RAGStreamEventType, DomainErrorCode


@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_pipeline():
    """Create mock RAG pipeline."""
    pipeline = MagicMock(spec=RAGPipeline)
    pipeline.answer_cache = AsyncMock()
    pipeline.retriever = AsyncMock()
    pipeline.prompt_builder = MagicMock()
    pipeline.llm_generator = AsyncMock()
    return pipeline


class TestStreamEndpoint:
    """Test streaming endpoint functionality."""
    
    @pytest.mark.asyncio
    async def test_stream_endpoint_success(self, client, monkeypatch):
        """Test successful streaming response."""
        
        # Mock the pipeline dependency
        mock_pipeline = MagicMock()
        mock_pipeline.answer_cache.get.return_value = None  # No cache hit
        
        async def mock_stream_answer(query, user_id=None, trace_id=None):
            # Simulate streaming tokens
            yield 'data: {"type": "token", "data": "Hello"}\n\n'
            yield 'data: {"type": "token", "data": " world"}\n\n'
            yield 'data: {"type": "done", "data": {"prompt_version": "v1", "sources_count": 2}}\n\n'
        
        # Mock the streaming service
        def mock_streaming_service_init(pipeline):
            service = MagicMock()
            service.stream_answer = mock_stream_answer
            return service
        
        monkeypatch.setattr("app.api.v1.routes.rag.RAGStreamingService", mock_streaming_service_init)
        monkeypatch.setattr("app.api.v1.routes.rag.get_rag_pipeline", lambda: mock_pipeline)
        
        # Make request
        response = client.post(
            "/rag/stream",
            json={"query": "Test query"},
            headers={"Accept": "text/event-stream"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Verify stream content
        content = response.text
        assert 'data: {"type": "token", "data": "Hello"}' in content
        assert 'data: {"type": "token", "data": " world"}' in content
        assert 'data: {"type": "done"' in content
    
    def test_stream_endpoint_validation_error(self, client, monkeypatch):
        """Test validation error for empty query."""
        
        mock_pipeline = MagicMock()
        monkeypatch.setattr("app.api.v1.routes.rag.get_rag_pipeline", lambda: mock_pipeline)
        
        response = client.post(
            "/rag/stream",
            json={"query": ""}
        )
        
        assert response.status_code == 400
        assert "validation_error" in response.json()["detail"]["error_code"]
    
    def test_stream_endpoint_query_too_long(self, client, monkeypatch):
        """Test validation error for query exceeding length limit."""
        
        mock_pipeline = MagicMock()
        monkeypatch.setattr("app.api.v1.routes.rag.get_rag_pipeline", lambda: mock_pipeline)
        
        # Create a query longer than 2000 characters
        long_query = "x" * 2001
        
        response = client.post(
            "/rag/stream",
            json={"query": long_query}
        )
        
        assert response.status_code == 400
        assert "validation_error" in response.json()["detail"]["error_code"]


class TestStreamEvents:
    """Test streaming event models."""
    
    def test_token_event_creation(self):
        """Test token event creation."""
        event = StreamTokenEvent(data="test token")
        assert event.type == RAGStreamEventType.TOKEN
        assert event.data == "test token"
        
        # Test JSON serialization
        json_data = event.model_dump_json()
        parsed = json.loads(json_data)
        assert parsed["type"] == "token"
        assert parsed["data"] == "test token"
    
    def test_done_event_creation(self):
        """Test done event creation."""
        event = StreamDoneEvent.create(
            total_tokens=50,
            sources_count=3,
            prompt_version="v1"
        )
        
        assert event.type == RAGStreamEventType.DONE
        assert event.data["total_tokens"] == 50
        assert event.data["sources_count"] == 3
        assert event.data["prompt_version"] == "v1"
    
    def test_done_event_with_guardrail(self):
        """Test done event with guardrail trigger."""
        event = StreamDoneEvent.create(
            sources_count=0,
            guardrail="no_context",
            prompt_version="v1"
        )
        
        assert event.data["guardrail"] == "no_context"
        assert event.data["sources_count"] == 0
    
    def test_error_event_creation(self):
        """Test error event creation."""
        event = StreamErrorEvent.create(
            error_code=DomainErrorCode.VALIDATION_ERROR,
            message="Query too long",
            details={"max_length": 2000}
        )
        
        assert event.type == RAGStreamEventType.ERROR
        assert event.data["error_code"] == "validation_error"
        assert event.data["message"] == "Query too long"
        assert event.data["max_length"] == 2000
        assert "prompt_version" in event.data


@pytest.mark.asyncio
class TestStreamingService:
    """Test streaming service functionality."""
    
    @pytest.fixture
    def mock_settings(self, monkeypatch):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.rag_max_query_length = 2000
        settings.rag_similarity_threshold = 0.55
        monkeypatch.setattr("app.infrastructure.ai.rag.streaming_service.get_settings", lambda: settings)
        return settings
    
    async def test_validate_query_empty(self, mock_settings):
        """Test query validation for empty query."""
        from app.infrastructure.ai.rag.streaming_service import RAGStreamingService
        from app.domain.exceptions import QueryValidationError
        
        pipeline = MagicMock()
        service = RAGStreamingService(pipeline)
        
        with pytest.raises(QueryValidationError, match="Query cannot be empty"):
            service._validate_query("")
    
    async def test_validate_query_too_long(self, mock_settings):
        """Test query validation for query exceeding length."""
        from app.infrastructure.ai.rag.streaming_service import RAGStreamingService
        from app.domain.exceptions import QueryValidationError
        
        pipeline = MagicMock()
        service = RAGStreamingService(pipeline)
        
        long_query = "x" * 2001
        
        with pytest.raises(QueryValidationError, match="Query length exceeds maximum"):
            service._validate_query(long_query)
    
    async def test_validate_query_success(self, mock_settings):
        """Test successful query validation."""
        from app.infrastructure.ai.rag.streaming_service import RAGStreamingService
        
        pipeline = MagicMock()
        service = RAGStreamingService(pipeline)
        
        # Should not raise
        service._validate_query("Valid query")


if __name__ == "__main__":
    pytest.main([__file__])