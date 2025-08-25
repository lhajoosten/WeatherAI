"""Unit tests for exception handlers."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError

from app.core.exception_handlers import (
    app_error_handler,
    weatherai_exception_handler, 
    rag_error_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler
)
from app.core.exceptions import AppError, ValidationError, NotFoundError, WeatherAIException
from app.ai.rag.exceptions import RAGError, LowSimilarityError


@pytest.fixture
def mock_request():
    """Mock FastAPI request."""
    request = MagicMock()
    request.url.path = "/test/path"
    return request


@pytest.mark.asyncio
async def test_app_error_handler(mock_request):
    """Test handling of AppError exceptions."""
    error = ValidationError("Invalid input", details="Field required")
    
    response = await app_error_handler(mock_request, error)
    
    assert response.status_code == 422
    content = response.body.decode()
    assert "Invalid input" in content
    assert "Field required" in content


@pytest.mark.asyncio  
async def test_not_found_error_handler(mock_request):
    """Test handling of NotFoundError."""
    error = NotFoundError("Document", "test-id")
    
    response = await app_error_handler(mock_request, error)
    
    assert response.status_code == 404
    content = response.body.decode()
    assert "Document not found" in content


@pytest.mark.asyncio
async def test_weatherai_exception_handler(mock_request):
    """Test handling of legacy WeatherAI exceptions."""
    error = WeatherAIException("Legacy error", status_code=503)
    
    response = await weatherai_exception_handler(mock_request, error)
    
    assert response.status_code == 503
    content = response.body.decode()
    assert "Legacy error" in content


@pytest.mark.asyncio
async def test_rag_error_handler_generic(mock_request):
    """Test handling of generic RAG errors."""
    error = RAGError("Generic RAG error")
    
    response = await rag_error_handler(mock_request, error)
    
    assert response.status_code == 500
    content = response.body.decode()
    assert "Generic RAG error" in content


@pytest.mark.asyncio
async def test_rag_error_handler_low_similarity(mock_request):
    """Test handling of LowSimilarityError."""
    error = LowSimilarityError("No similar documents")
    
    response = await rag_error_handler(mock_request, error)
    
    assert response.status_code == 422
    content = response.body.decode()
    assert "low_similarity_error" in content


@pytest.mark.asyncio
async def test_http_exception_handler(mock_request):
    """Test handling of HTTP exceptions."""
    error = HTTPException(status_code=404, detail="Not found")
    
    response = await http_exception_handler(mock_request, error)
    
    assert response.status_code == 404
    content = response.body.decode()
    assert "Not found" in content


@pytest.mark.asyncio
async def test_validation_exception_handler(mock_request):
    """Test handling of validation errors."""
    # Mock validation error structure
    error = RequestValidationError([
        {
            "loc": ["body", "field"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ])
    
    response = await validation_exception_handler(mock_request, error)
    
    assert response.status_code == 422
    content = response.body.decode()
    assert "Validation failed" in content
    assert "field required" in content


@pytest.mark.asyncio
async def test_global_exception_handler(mock_request):
    """Test handling of unexpected exceptions."""
    error = RuntimeError("Unexpected error")
    
    response = await global_exception_handler(mock_request, error)
    
    assert response.status_code == 500
    content = response.body.decode()
    assert "Internal Server Error" in content