from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.redis_client import redis_client
from app.core.exception_handlers import register_exception_handlers
from app.db.database import close_db
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

    # Database initialization is handled by entrypoint.sh
    logger.info("Database initialization handled by entrypoint bootstrap")

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


# Register centralized exception handlers
register_exception_handlers(app)

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
