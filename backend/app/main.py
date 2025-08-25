from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.redis_client import redis_client
from app.db.database import close_db
from app.schemas.dto import ErrorDetail, ValidationErrorResponse
from app.workers.scheduler import analytics_scheduler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting WeatherAI backend...")

    # Initialize Redis (optional, fails gracefully)
    try:
        await redis_client.initialize()
    except Exception as e:
        logger.warning(
            "Redis initialization failed, continuing with fallback modes",
            error=str(e)
        )

    # Start analytics scheduler
    await analytics_scheduler.start()

    logger.info("WeatherAI backend started successfully")
    yield

    # Shutdown
    logger.info("Shutting down WeatherAI backend...")

    # Stop analytics scheduler
    await analytics_scheduler.stop()
    
    # Close Redis connection
    await redis_client.close()

    await close_db()
    logger.info("WeatherAI backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WeatherAI Backend",
    description="AI-powered weather application backend with FastAPI, MSSQL, and OpenAI LLM",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed error information."""
    return JSONResponse(
        status_code=422,
        content=ValidationErrorResponse(
            detail="Validation failed",
            errors=[
                {
                    "loc": list(error["loc"]),
                    "msg": error["msg"],
                    "type": error["type"]
                }
                for error in exc.errors()
            ] # type: ignore
        ).dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
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


# Include API routes
app.include_router(api_router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WeatherAI Backend API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/health"
    }
