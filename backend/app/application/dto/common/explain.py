"""Explain service response schemas."""

from pydantic import BaseModel


class ExplainResponse(BaseModel):
    """Response schema for weather explanation service."""
    summary: str
    actions: list[str]
    driver: str
    tokens_in: int
    tokens_out: int
    model: str