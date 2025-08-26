"""Schemas module - centralized Pydantic models.

This module provides organized schema definitions split by domain:
- common: Shared schemas (errors, health, explain)  
- user: User authentication and profile schemas
- location: Location and location group schemas
- rag: RAG system request/response schemas

For backward compatibility, commonly used schemas are re-exported here.
"""

# Re-export commonly used schemas for backward compatibility
from .common import ErrorDetail, ValidationErrorDetail, ValidationErrorResponse, HealthResponse, ExplainResponse

# Import all domain-specific schemas
from . import common, user, location, rag

__all__ = [
    # Backward compatibility exports
    "ErrorDetail",
    "ValidationErrorDetail", 
    "ValidationErrorResponse",
    "HealthResponse",
    "ExplainResponse",
    # Domain modules
    "common",
    "user", 
    "location",
    "rag",
]
