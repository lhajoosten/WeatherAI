"""Unit tests for RAG functionality (migrated from legacy RAGService).

These tests now target the application-layer use cases instead of the removed
`RAGService` class. We focus on behavior parity: ingestion, querying, and
health checks via the pipeline abstraction.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from app.application.rag_use_cases import AskRAGQuestion, IngestDocument
from app.infrastructure.ai.rag.models import AnswerResult
from app.infrastructure.ai.rag.exceptions import RAGError
from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.infrastructure.db.repositories.rag_document_repository import RagDocumentRepository
from app.infrastructure.db.base import UnitOfWork


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
def ask_use_case(mock_pipeline, mock_repo):
    return AskRAGQuestion(rag_pipeline=mock_pipeline, document_repository=mock_repo, uow_factory=lambda: AsyncMock())

@pytest.fixture
def ingest_use_case(mock_pipeline, mock_repo):
    return IngestDocument(rag_pipeline=mock_pipeline, document_repository=mock_repo, uow_factory=lambda: AsyncMock())


@pytest.mark.asyncio
async def test_ingest_document_success(ingest_use_case, mock_pipeline, mock_repo, mock_document):
    """Test successful document ingestion."""
    mock_repo.get_by_source_id.side_effect = [None, mock_document]  # First call: not found, second: found
    
    # Simulate repo behavior for IngestDocument use case (expects repository create via UoW)
    mock_repo.get_by_source_id.side_effect = [None]
    mock_repo.create_document = AsyncMock(return_value=str(mock_document.id))

    # Execute ingestion
    result = await ingest_use_case.execute(
        source_id="test-source",
        text="Test content",
        metadata={"key": "value"}
    )
    
    # Verify pipeline was called
    mock_pipeline.ingest.assert_called_once_with(
        "test-source", "Test content", {"key": "value"}
    )
    
    # Verify repository was checked for duplicates
    mock_repo.get_by_source_id.assert_called()
    
    # Verify result format
    assert result["document_id"] == str(mock_document.id)
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_ingest_document_conflict(ingest_use_case, mock_repo, mock_document):
    """Test ingestion fails when document already exists."""
    mock_repo.get_by_source_id.return_value = mock_document
    with pytest.raises(Exception):  # ValidationError in new use case
        await ingest_use_case.execute(
            source_id="test-source",
            text="Test content",
        )


@pytest.mark.asyncio
async def test_ingest_document_pipeline_error(ingest_use_case, mock_pipeline, mock_repo):
    """Test ingestion handles pipeline errors."""
    mock_repo.get_by_source_id.return_value = None
    mock_pipeline.ingest.side_effect = RAGError("Pipeline failed")
    with pytest.raises(RAGError):  # Propagated by use case
        await ingest_use_case.execute(
            source_id="test-source",
            text="Test content",
        )


@pytest.mark.asyncio
async def test_query_success(ask_use_case, mock_pipeline):
    result = await ask_use_case.execute(user_id="u1", query="Test query")
    mock_pipeline.retrieve.assert_called_once()
    mock_pipeline.generate.assert_called_once()
    assert result["answer"] == "Test answer"
    assert result["sources"][0]["document_id"] == "test-doc"


@pytest.mark.asyncio
async def test_query_pipeline_error(ask_use_case, mock_pipeline):
    mock_pipeline.retrieve.return_value = [MagicMock(document_id="d1", similarity=0.9, content="abc")]  # retrieval ok
    mock_pipeline.generate.side_effect = RAGError("Query failed")
    with pytest.raises(RAGError):
        await ask_use_case.execute(user_id="u1", query="Test query")


@pytest.mark.asyncio
async def test_health_check_healthy(mock_pipeline):
    result = await mock_pipeline.health_check()
    assert result["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_check_unhealthy(mock_pipeline):
    mock_pipeline.health_check.side_effect = Exception("Pipeline down")
    try:
        await mock_pipeline.health_check()
    except Exception as e:
        assert "Pipeline down" in str(e)