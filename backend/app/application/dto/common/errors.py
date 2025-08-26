"""Error response schemas."""

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Standard error response format."""
    type: str
    title: str
    detail: str
    status: int


class ValidationErrorDetail(BaseModel):
    """Individual validation error detail."""
    loc: list[str]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    """Validation error response with detailed error information."""
    type: str = "validation_error"
    title: str = "Validation Error"
    detail: str
    status: int = 422
    errors: list[ValidationErrorDetail]