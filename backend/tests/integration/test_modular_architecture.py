"""Integration tests for the modularized architecture.

This module tests the integration between layers and ensures
the domain events, use cases, and error handling work together.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.event_bus import EventBus
from app.application.rag_use_cases import AskRAGQuestion, IngestDocument
from app.domain.events import RAGQueryAnsweredEvent, DataIngestedEvent
from app.domain.exceptions import ValidationError, NotFoundError
from app.core.metrics import get_metrics_sink, record_metric
from app.core.logging import get_rag_logger


class TestIntegrationFlow:
    """Integration tests for the complete RAG flow."""
    
    @pytest.fixture
    def mock_rag_pipeline(self):
        """Mock RAG pipeline for testing."""
        pipeline = AsyncMock()
        
        # Mock retrieve method
        mock_doc = MagicMock()
        mock_doc.document_id = "doc_123"
        mock_doc.similarity = 0.85
        mock_doc.content = "Weather data shows temperatures rising."
        
        pipeline.retrieve.return_value = [mock_doc]
        
        # Mock generate method
        mock_answer = MagicMock()
        mock_answer.answer = "Based on the weather data, temperatures are rising."
        pipeline.generate.return_value = mock_answer
        
        return pipeline
    
    @pytest.fixture
    def mock_document_repository(self):
        """Mock document repository for testing."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_uow_factory(self):
        """Mock Unit of Work factory for testing."""
        mock_uow = AsyncMock()
        mock_uow.get_repository = AsyncMock()
        mock_uow.commit = AsyncMock()
        
        async def uow_context():
            return mock_uow
        
        mock_factory = AsyncMock()
        mock_factory.return_value.__aenter__ = uow_context
        mock_factory.return_value.__aexit__ = AsyncMock(return_value=None)
        
        return mock_factory
    
    @pytest.fixture
    def event_bus(self):
        """Clean event bus for testing."""
        bus = EventBus()
        # Register a test handler to capture events
        bus.captured_events = []
        
        def capture_event(event):
            bus.captured_events.append(event)
        
        bus.register_handler("rag.query.answered", capture_event)
        bus.register_handler("data.ingested", capture_event)
        
        return bus
    
    @pytest.fixture
    def ask_rag_use_case(self, mock_rag_pipeline, mock_document_repository, mock_uow_factory):
        """Create AskRAGQuestion use case with mocked dependencies."""
        return AskRAGQuestion(
            rag_pipeline=mock_rag_pipeline,
            document_repository=mock_document_repository,
            uow_factory=mock_uow_factory
        )
    
    @pytest.mark.asyncio
    async def test_complete_rag_query_flow(self, ask_rag_use_case, event_bus):
        """Test complete RAG query flow with event publishing."""
        # Clear metrics
        get_metrics_sink().clear()
        
        # Execute the use case
        result = await ask_rag_use_case.execute(
            user_id="user_123",
            query="What is the weather like?",
            max_sources=5,
            min_similarity=0.7
        )
        
        # Verify the result structure
        assert "answer" in result
        assert "sources" in result
        assert "metadata" in result
        
        assert result["answer"] == "Based on the weather data, temperatures are rising."
        assert len(result["sources"]) == 1
        assert result["sources"][0]["document_id"] == "doc_123"
        assert result["sources"][0]["similarity"] == 0.85
        
        # Verify metadata
        metadata = result["metadata"]
        assert metadata["query_length"] == len("What is the weather like?")
        assert metadata["answer_length"] == len(result["answer"])
        assert metadata["sources_count"] == 1
        
        # Verify domain event was published
        assert len(event_bus.captured_events) == 1
        event = event_bus.captured_events[0]
        assert isinstance(event, RAGQueryAnsweredEvent)
        assert event.aggregate_id == "user_123"
        assert event.query == "What is the weather like?"
        
        # Verify metrics were recorded (this tests the integration)
        metrics = get_metrics_sink().get_metrics("rag.query.length")
        assert len(metrics) > 0
    
    @pytest.mark.asyncio
    async def test_rag_query_validation_error(self, ask_rag_use_case):
        """Test RAG query validation with domain exceptions."""
        # Test empty query
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            await ask_rag_use_case.execute(
                user_id="user_123",
                query="",  # Empty query should raise ValidationError
                max_sources=5,
                min_similarity=0.7
            )
        
        # Test whitespace-only query
        with pytest.raises(ValidationError, match="Query cannot be empty"):
            await ask_rag_use_case.execute(
                user_id="user_123",
                query="   ",  # Whitespace-only query
                max_sources=5,
                min_similarity=0.7
            )
    
    @pytest.mark.asyncio
    async def test_rag_query_no_documents_found(self, mock_rag_pipeline, mock_document_repository, mock_uow_factory):
        """Test RAG query when no relevant documents are found."""
        # Configure pipeline to return no documents
        mock_rag_pipeline.retrieve.return_value = []
        
        use_case = AskRAGQuestion(
            rag_pipeline=mock_rag_pipeline,
            document_repository=mock_document_repository,
            uow_factory=mock_uow_factory
        )
        
        with pytest.raises(NotFoundError, match="No relevant documents found for query"):
            await use_case.execute(
                user_id="user_123",
                query="What is the weather like?",
                max_sources=5,
                min_similarity=0.7
            )
    
    @pytest.mark.asyncio
    async def test_document_ingestion_flow(self, mock_rag_pipeline, mock_document_repository, mock_uow_factory, event_bus):
        """Test document ingestion use case flow."""
        # Setup mocks
        mock_rag_pipeline.ingest.return_value = MagicMock(chunks=["chunk1", "chunk2"])
        mock_document_repository.get_by_source_id.return_value = None  # Document doesn't exist
        
        # Mock the repository creation
        mock_repo = AsyncMock()
        mock_repo.create_document.return_value = "doc_456"
        mock_uow_factory.return_value.__aenter__.return_value.get_repository.return_value = mock_repo
        
        ingest_use_case = IngestDocument(
            rag_pipeline=mock_rag_pipeline,
            document_repository=mock_document_repository,
            uow_factory=mock_uow_factory
        )
        
        # Execute ingestion
        result = await ingest_use_case.execute(
            source_id="weather_report_123",
            text="Weather report content here",
            metadata={"type": "weather", "source": "api"}
        )
        
        # Verify result
        assert result["document_id"] == "doc_456"
        assert result["source_id"] == "weather_report_123"
        assert result["chunks_count"] == 2
        assert result["status"] == "success"
        
        # Verify domain event was published
        assert len(event_bus.captured_events) == 1
        event = event_bus.captured_events[0]
        assert isinstance(event, DataIngestedEvent)
        assert event.aggregate_id == "weather_report_123"
        assert event.provider == "rag_ingestion"
        assert event.record_count == 2
    
    @pytest.mark.asyncio
    async def test_logging_integration(self, caplog):
        """Test that structured logging works across the system."""
        # Get a logger with tag
        logger = get_rag_logger(__name__, user_id="test_user")
        
        # Log some events
        logger.info("Starting RAG query", query="test query")
        logger.warning("Low similarity score", similarity=0.3, threshold=0.7)
        
        # Check that logs contain structured data
        # Note: In a real test, you'd configure structured logging to capture
        # the actual JSON structure, but this demonstrates the API
        assert "Starting RAG query" in caplog.text
        assert "Low similarity score" in caplog.text
    
    def test_metrics_integration(self):
        """Test metrics collection across the system."""
        # Clear existing metrics
        sink = get_metrics_sink()
        sink.clear()
        
        # Record some metrics
        record_metric("test.counter", 1, {"operation": "test"})
        record_metric("test.duration", 0.5, {"operation": "test"})
        record_metric("test.counter", 1, {"operation": "test"})
        
        # Verify metrics are recorded
        counter_metrics = sink.get_metrics("test.counter")
        duration_metrics = sink.get_metrics("test.duration")
        
        assert len(counter_metrics) == 2
        assert len(duration_metrics) == 1
        
        # Verify summary
        summary = sink.get_summary()
        assert summary["test.counter"] == 2
        assert summary["test.duration"] == 1
    
    def test_value_objects_integration(self):
        """Test domain value objects work correctly."""
        from app.domain.value_objects import Coordinates, Temperature, LocationId
        
        # Test coordinates
        coords = Coordinates(52.3676, 4.9041)  # Amsterdam
        assert coords.latitude == 52.3676
        assert coords.longitude == 4.9041
        
        # Test temperature conversion
        temp_c = Temperature(20.0, "celsius")
        temp_f = Temperature(68.0, "fahrenheit")
        
        converted = temp_f.to_celsius()
        assert abs(converted.value - temp_c.value) < 0.1
        
        # Test location ID
        location_id = LocationId(123)
        assert location_id.value == 123
        
        # Test validation
        with pytest.raises(ValueError):
            LocationId(-1)  # Invalid location ID