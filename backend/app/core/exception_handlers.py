"""Central exception handlers for mapping domain exceptions to HTTP responses."""

import structlog
from typing import Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.exceptions import AppError, WeatherAIException
from app.ai.rag.exceptions import RAGError, LowSimilarityError, EmptyContextError
from app.schemas.common.errors import ErrorDetail, ValidationErrorResponse, ValidationErrorDetail

logger = structlog.get_logger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle AppError exceptions with structured response."""
    logger.warning(
        "Application error occurred",
        error_type=type(exc).__name__,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(
            type=type(exc).__name__.lower().replace("error", "_error"),
            title=exc.message,
            detail=exc.details or exc.message,
            status=exc.status_code
        ).dict()
    )


async def weatherai_exception_handler(request: Request, exc: WeatherAIException) -> JSONResponse:
    """Handle legacy WeatherAIException for backward compatibility."""
    logger.warning(
        "Legacy WeatherAI exception occurred",
        error_type=type(exc).__name__,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(
            type=type(exc).__name__.lower().replace("exception", "_error"),
            title=exc.message,
            detail=exc.message,
            status=exc.status_code
        ).dict()
    )


async def rag_error_handler(request: Request, exc: RAGError) -> JSONResponse:
    """Handle RAG-specific exceptions."""
    # Map specific RAG errors to appropriate status codes
    if isinstance(exc, LowSimilarityError):
        status_code = 422
        error_type = "low_similarity_error"
    elif isinstance(exc, EmptyContextError):
        status_code = 422
        error_type = "empty_context_error"
    else:
        status_code = 500
        error_type = "rag_error"
    
    logger.warning(
        "RAG error occurred",
        error_type=type(exc).__name__,
        message=str(exc),
        status_code=status_code,
        path=request.url.path
    )
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorDetail(
            type=error_type,
            title=str(exc),
            detail=str(exc),
            status=status_code
        ).dict()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(
            type="http_error",
            title=exc.detail,
            detail=exc.detail,
            status=exc.status_code
        ).dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors with detailed error information."""
    return JSONResponse(
        status_code=422,
        content=ValidationErrorResponse(
            detail="Validation failed",
            errors=[
                ValidationErrorDetail(
                    loc=list(error["loc"]),
                    msg=error["msg"],
                    type=error["type"]
                )
                for error in exc.errors()
            ]
        ).dict()
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error("Unexpected error", exc_info=exc, extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content=ErrorDetail(
            type="internal_error",
            title="Internal Server Error",
            detail="An unexpected error occurred",
            status=500
        ).dict()
    )


def register_exception_handlers(app: Any) -> None:
    """Register all exception handlers with the FastAPI app."""
    # Domain exception handlers (order matters - most specific first)
    app.add_exception_handler(RAGError, rag_error_handler)
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(WeatherAIException, weatherai_exception_handler)
    
    # HTTP and validation handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    
    # Global fallback
    app.add_exception_handler(Exception, global_exception_handler)