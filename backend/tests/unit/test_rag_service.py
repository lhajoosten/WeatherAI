"""Unit tests for RAG service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from app.services.rag_service import RAGService
from app.ai.rag.models import AnswerResult
from app.ai.rag.exceptions import RAGError
from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.repositories.rag import RagDocumentRepository
from app.repositories.base import UnitOfWork


@pytest.fixture
def mock_pipeline():
    """Mock RAG pipeline."""
    pipeline = AsyncMock()
    pipeline.ingest.return_value = {
        "document_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunks": 5,
        "status": "success"
    }
    pipeline.answer.return_value = AnswerResult(
        answer="Test answer",
        sources=[{"source_id": "test-doc", "score": 0.9}],
        metadata={"model": "gpt-4"}
    )
    pipeline.health_check.return_value = {"status": "healthy"}
    return pipeline


@pytest.fixture
def mock_document():
    """Mock document from repository."""
    doc = MagicMock()
    doc.id = UUID("550e8400-e29b-41d4-a716-446655440000")
    doc.source_id = "test-source"
    return doc


@pytest.fixture
def mock_repo():
    """Mock RAG document repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_uow(mock_repo):
    """Mock Unit of Work."""
    uow = MagicMock()  # Use MagicMock instead of AsyncMock
    uow.get_repository.return_value = mock_repo  # Return the mock repo directly
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    return uow


@pytest.fixture
def rag_service(mock_pipeline):
    """RAG service instance."""
    return RAGService(mock_pipeline)


@pytest.mark.asyncio
async def test_ingest_document_success(rag_service, mock_pipeline, mock_repo, mock_uow, mock_document):
    """Test successful document ingestion."""
    mock_repo.get_by_source_id.side_effect = [None, mock_document]  # First call: not found, second: found
    
    result = await rag_service.ingest_document(
        source_id="test-source",
        text="Test content",
        metadata={"key": "value"},
        uow=mock_uow
    )
    
    # Verify pipeline was called
    mock_pipeline.ingest.assert_called_once_with(
        "test-source", "Test content", {"key": "value"}
    )
    
    # Verify repository was checked for duplicates
    mock_repo.get_by_source_id.assert_called()
    
    # Verify result format
    assert result["document_id"] == str(mock_document.id)
    assert result["chunks"] == 5
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_ingest_document_conflict(rag_service, mock_repo, mock_uow, mock_document):
    """Test ingestion fails when document already exists."""
    mock_repo.get_by_source_id.return_value = mock_document  # Document exists
    
    with pytest.raises(ConflictError) as exc_info:
        await rag_service.ingest_document(
            source_id="test-source",
            text="Test content",
            uow=mock_uow
        )
    
    assert "already exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_ingest_document_pipeline_error(rag_service, mock_pipeline, mock_repo, mock_uow):
    """Test ingestion handles pipeline errors."""
    mock_repo.get_by_source_id.return_value = None  # No existing document
    mock_pipeline.ingest.side_effect = RAGError("Pipeline failed")
    
    with pytest.raises(ServiceUnavailableError) as exc_info:
        await rag_service.ingest_document(
            source_id="test-source", 
            text="Test content",
            uow=mock_uow
        )
    
    assert "RAG Pipeline" in str(exc_info.value)


@pytest.mark.asyncio
async def test_query_success(rag_service, mock_pipeline):
    """Test successful query."""
    result = await rag_service.query("Test query")
    
    mock_pipeline.answer.assert_called_once_with("Test query")
    assert result.answer == "Test answer"
    assert len(result.sources) == 1
    assert result.sources[0]["source_id"] == "test-doc"


@pytest.mark.asyncio
async def test_query_pipeline_error(rag_service, mock_pipeline):
    """Test query handles pipeline errors."""
    mock_pipeline.answer.side_effect = RAGError("Query failed")
    
    with pytest.raises(ServiceUnavailableError) as exc_info:
        await rag_service.query("Test query")
    
    assert "RAG Pipeline" in str(exc_info.value)


@pytest.mark.asyncio
async def test_health_check_healthy(rag_service, mock_pipeline):
    """Test health check when system is healthy."""
    result = await rag_service.health_check()
    
    mock_pipeline.health_check.assert_called_once()
    assert result["status"] == "healthy"
    assert result["service"] == "operational"


@pytest.mark.asyncio
async def test_health_check_unhealthy(rag_service, mock_pipeline):
    """Test health check when pipeline fails."""
    mock_pipeline.health_check.side_effect = Exception("Pipeline down")
    
    result = await rag_service.health_check()
    
    assert result["status"] == "unhealthy"
    assert result["service"] == "degraded"
    assert "Pipeline down" in result["error"]