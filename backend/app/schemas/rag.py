"""Pydantic schemas for RAG API endpoints."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class IngestRequest(BaseModel):
    """Request schema for document ingestion."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_id": "weather-guide-2024",
                "text": "Weather forecasting involves analyzing atmospheric conditions...",
                "metadata": {
                    "author": "Weather Service",
                    "category": "documentation",
                    "version": "1.0"
                }
            }
        }
    )
    
    source_id: str = Field(..., description="Unique identifier for the document source")
    text: str = Field(..., description="Text content to ingest")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")


class SourceDTO(BaseModel):
    """Source information in query responses."""
    source_id: str = Field(..., description="Source document identifier")
    score: float = Field(..., description="Similarity score (0-1)")
    content_preview: Optional[str] = Field(default=None, description="Preview of relevant content")


class IngestResponse(BaseModel):
    """Response schema for document ingestion."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "chunks": 15,
                "status": "success"
            }
        }
    )
    
    document_id: str = Field(..., description="UUID of the created document")
    chunks: int = Field(..., description="Number of chunks created")
    status: str = Field(..., description="Ingestion status")


class QueryRequest(BaseModel):
    """Request schema for RAG queries."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "What are the main factors that affect weather forecasting accuracy?"
            }
        }
    )
    
    query: str = Field(..., description="User question or query")


class QueryResponse(BaseModel):
    """Response schema for RAG queries."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "Weather forecasting accuracy is primarily affected by atmospheric complexity, data quality, and model resolution...",
                "sources": [
                    {
                        "source_id": "weather-guide-2024",
                        "score": 0.89,
                        "content_preview": "Atmospheric conditions are complex and dynamic..."
                    }
                ],
                "metadata": {
                    "num_chunks": 3,
                    "model": "gpt-4",
                    "prompt_version": "qa_v1"
                }
            }
        }
    )
    
    answer: str = Field(..., description="Generated answer")
    sources: List[SourceDTO] = Field(..., description="List of sources used for the answer")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ErrorResponse(BaseModel):
    """Error response schema."""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "No relevant content found",
                "details": "All retrieved documents have similarity below threshold 0.75"
            }
        }
    )
    
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")