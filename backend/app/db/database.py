"""Database session management for WeatherAI backend.

This module provides database engine configuration, session management,
and connection utilities for the FastAPI application. Handles async
SQLAlchemy sessions with proper lifecycle management.

Key components:
- Async engine configuration for MSSQL
- Session factory with dependency injection support
- Database connection management utilities
"""

import logging
import urllib.parse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create async engine for MSSQL (engine remains module-global)
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,  # Use NullPool for better compatibility with pyodbc
    echo=settings.sqlalchemy_echo,
)

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


def _build_sync_master_url() -> str:
    """Build a sync pyodbc URL that connects to the 'master' database (for CREATE DATABASE)."""
    odbc_params = {
        "DRIVER": "{ODBC Driver 18 for SQL Server}",
        "SERVER": f"{settings.db_server},{settings.db_port}",
        "DATABASE": "master",
        "UID": settings.db_user,
        "PWD": settings.db_password,
        "TrustServerCertificate": "yes",
    }
    odbc_connect = ";".join([f"{k}={v}" for k, v in odbc_params.items()])
    encoded = urllib.parse.quote_plus(odbc_connect)
    return f"mssql+pyodbc:///?odbc_connect={encoded}"


async def close_db():
    """Close database engine."""
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed")
