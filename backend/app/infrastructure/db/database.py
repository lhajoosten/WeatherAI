"""Database session management for WeatherAI backend.

This module provides database engine configuration, session management,
and connection utilities for the FastAPI application. Handles async
SQLAlchemy sessions with proper lifecycle management.

Key components:
- Async engine configuration for PostgreSQL
- Session factory with dependency injection support
- Database connection management utilities
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create async engine for PostgreSQL
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,  # Use NullPool for better compatibility during development
    echo=settings.sqlalchemy_echo,
)

# Log database connection info (sanitized)
db_url_safe = settings.database_url.split('@')[0].split('//')[1].split(':')[0]
logger.info(f"[DB] dialect=postgres url=postgresql://{db_url_safe}@... (sanitized)")

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db():
    """Close database engine."""
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed")
