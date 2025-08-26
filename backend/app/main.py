from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.error_handlers import register_error_handlers
from app.core.settings import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import initialize_prometheus_metrics, is_prometheus_enabled
from app.core.tracing import configure_tracing, instrument_app, instrument_httpx
from app.core.middleware import ObservabilityMiddleware
from app.core.redis_client import redis_client
from app.infrastructure.db.database import close_db
from app.application.event_bus import register_default_handlers
from app.infrastructure.background.scheduler import AnalyticsScheduler

# Configure structured logging with service name
configure_logging(level="INFO", json_logs=True, service_name="weatherai-backend")
logger = get_logger(__name__)

# Get centralized settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Startup
    logger.info("Starting WeatherAI backend...")

    # Initialize observability components
    logger.info("Initializing observability components...")
    
    # Initialize tracing
    tracer = configure_tracing(
        service_name="weatherai-backend",
        otlp_endpoint=settings.otlp_endpoint if hasattr(settings, 'otlp_endpoint') else None,
        environment=settings.environment if hasattr(settings, 'environment') else "development"
    )
    if tracer:
        logger.info("OpenTelemetry tracing initialized")
    
    # Initialize Prometheus metrics
    if is_prometheus_enabled():
        prometheus_metrics = initialize_prometheus_metrics()
        if prometheus_metrics:
            logger.info("Prometheus metrics initialized")
    else:
        logger.info("Prometheus metrics disabled")
    
    # Instrument HTTPX for outbound tracing
    instrument_httpx()

    # Register domain event handlers
    register_default_handlers()
    logger.info("Domain event handlers registered")

    # Initialize Redis (optional, fails gracefully)
    try:
        await redis_client.initialize()
        logger.info("Redis initialized successfully")
    except Exception as e:
        logger.warning(
            "Redis initialization failed, continuing with fallback modes",
            error=str(e)
        )

    # Database initialization is handled by entrypoint.sh
    logger.info("Database initialization handled by entrypoint bootstrap")

    # Start analytics scheduler
    await AnalyticsScheduler().start()
    logger.info("Analytics scheduler started")

    logger.info("WeatherAI backend started successfully")
    yield

    # Shutdown
    logger.info("Shutting down WeatherAI backend...")

    # Stop analytics scheduler
    await AnalyticsScheduler().stop()
    logger.info("Analytics scheduler stopped")

    # Close Redis connection
    await redis_client.close()
    logger.info("Redis connection closed")

    await close_db()
    logger.info("WeatherAI backend shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WeatherAI Backend",
    description="AI-powered weather application backend with FastAPI, MSSQL, and OpenAI LLM",
    version="0.1.0",
    lifespan=lifespan
)

# Add observability middleware (before CORS)
app.add_middleware(
    ObservabilityMiddleware,
    service_name="weatherai-backend",
    exclude_paths=["/health", "/metrics", "/docs", "/openapi.json"]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI with OpenTelemetry after middleware setup
instrument_app(app)


# Register centralized exception handlers
register_error_handlers(app)

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
