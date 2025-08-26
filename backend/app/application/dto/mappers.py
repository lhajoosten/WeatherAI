"""Schema mappers for converting between domain entities and API DTOs.

This module provides mapping functions to convert between internal domain
models and external API schemas, keeping the layers properly separated.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.domain.value_objects import LocationId, UserId, Coordinates, Temperature


def map_user_to_response(user_domain_entity) -> Dict[str, Any]:
    """Map a user domain entity to API response schema."""
    return {
        "id": user_domain_entity.id,
        "email": user_domain_entity.email,
        "created_at": user_domain_entity.created_at.isoformat() if user_domain_entity.created_at else None,
        "timezone": getattr(user_domain_entity, 'timezone', None)
    }


def map_location_to_response(location_domain_entity) -> Dict[str, Any]:
    """Map a location domain entity to API response schema."""
    return {
        "id": location_domain_entity.id,
        "name": location_domain_entity.name,
        "latitude": location_domain_entity.lat,
        "longitude": location_domain_entity.lon,
        "timezone": getattr(location_domain_entity, 'timezone', None),
        "created_at": location_domain_entity.created_at.isoformat() if location_domain_entity.created_at else None
    }


def map_coordinates_from_request(latitude: float, longitude: float) -> Coordinates:
    """Map request coordinates to domain value object."""
    return Coordinates(latitude=latitude, longitude=longitude)


def map_temperature_to_response(temp: Temperature) -> Dict[str, Any]:
    """Map temperature value object to API response."""
    return {
        "value": temp.value,
        "unit": temp.unit
    }


def map_rag_document_to_response(document_entity) -> Dict[str, Any]:
    """Map RAG document entity to API response schema."""
    return {
        "id": document_entity.id,
        "source_id": document_entity.source_id,
        "text": document_entity.text,
        "metadata": document_entity.metadata or {},
        "created_at": document_entity.created_at.isoformat() if document_entity.created_at else None,
        "chunks_count": getattr(document_entity, 'chunks_count', 0)
    }


def map_rag_query_result(
    answer: str,
    sources: List[Dict[str, Any]],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Map RAG query result to API response schema."""
    return {
        "answer": answer,
        "sources": sources,
        "metadata": {
            "query_length": metadata.get("query_length", 0),
            "answer_length": len(answer),
            "sources_count": len(sources),
            "timestamp": datetime.utcnow().isoformat()
        }
    }


def map_error_to_response(
    error: Exception,
    status_code: int = 500,
    include_details: bool = False
) -> Dict[str, Any]:
    """Map domain exception to API error response."""
    response = {
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "status_code": status_code
        }
    }
    
    if include_details and hasattr(error, 'details') and error.details:
        response["error"]["details"] = error.details
    
    if hasattr(error, 'extra_data') and error.extra_data:
        response["error"]["extra_data"] = error.extra_data
    
    return response


def map_validation_errors_to_response(errors: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Map validation errors to API response schema."""
    return {
        "error": {
            "type": "ValidationError",
            "message": "Validation failed",
            "status_code": 422,
            "validation_errors": errors
        }
    }


def map_pagination_metadata(
    total: int,
    limit: int,
    offset: int,
    items_count: int
) -> Dict[str, Any]:
    """Map pagination data to API response metadata."""
    return {
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "returned": items_count,
            "has_more": offset + items_count < total,
            "next_offset": offset + limit if offset + items_count < total else None
        }
    }