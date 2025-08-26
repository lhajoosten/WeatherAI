"""Centralized error handlers for mapping domain exceptions to HTTP responses.

This module registers exception handlers that convert domain exceptions
into appropriate HTTP responses with consistent error format.
"""

from __future__ import annotations
from typing import Union

import structlog
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import (
    DomainError,
    ValidationError,
    NotFoundError,
    ConflictError,
    BusinessRuleViolationError,
    ForecastUnavailableError,
    RAGError,
    LowSimilarityError
)
from app.infrastructure.security.rate_limiter import RateLimitExceededError
from app.application.dto.mappers import map_error_to_response, map_validation_errors_to_response


logger = structlog.get_logger(__name__)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """Handle domain exceptions with appropriate HTTP status codes."""
    
    # Map domain exceptions to HTTP status codes
    status_map = {
        ValidationError: 422,
        NotFoundError: 404,
        ConflictError: 409,
        BusinessRuleViolationError: 422,
        ForecastUnavailableError: 503,
        RAGError: 500,
        LowSimilarityError: 422,
    }
    
    status_code = status_map.get(type(exc), 500)
    
    logger.warning(
        "Domain error occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        status_code=status_code,
        path=request.url.path
    )
    
    response = map_error_to_response(
        error=exc,
        status_code=status_code,
        include_details=True
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response
    )


async def rate_limit_error_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    
    logger.warning(
        "Rate limit exceeded",
        limit=exc.limit,
        window_seconds=exc.window_seconds,
        retry_after=exc.retry_after,
        path=request.url.path
    )
    
    response = map_error_to_response(
        error=exc,
        status_code=429,
        include_details=True
    )
    
    return JSONResponse(
        status_code=429,
        content=response,
        headers={"Retry-After": str(exc.retry_after)}
    )


async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]) -> JSONResponse:
    """Handle HTTP exceptions."""
    
    logger.info(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )
    
    response = {
        "error": {
            "type": "HTTPException",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    
    logger.info(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path
    )
    
    # Convert pydantic errors to our format
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    response = map_validation_errors_to_response(validation_errors)
    
    return JSONResponse(
        status_code=422,
        content=response
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    
    logger.error(
        "Unexpected error occurred",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        exc_info=True
    )
    
    response = {
        "error": {
            "type": "InternalServerError",
            "message": "An internal server error occurred",
            "status_code": 500
        }
    }
    
    return JSONResponse(
        status_code=500,
        content=response
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all error handlers with the FastAPI application."""
    
    # Domain exception handlers
    app.add_exception_handler(DomainError, domain_error_handler)
    
    # Security exception handlers
    app.add_exception_handler(RateLimitExceededError, rate_limit_error_handler)
    
    # HTTP exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    
    # Validation exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Error handlers registered successfully")