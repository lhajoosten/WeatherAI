"""Health check response schemas."""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, Any]