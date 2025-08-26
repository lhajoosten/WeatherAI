"""RAG request schemas."""

from typing import Dict, Any, Optional
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