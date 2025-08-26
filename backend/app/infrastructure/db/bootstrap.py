"""Database bootstrap functionality for PostgreSQL.

Note: PostgreSQL databases are typically created via docker-compose or deployment scripts.
This module provides basic connectivity testing.
"""

import logging
import structlog
import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
std_logger = logging.getLogger(__name__)


async def test_database_connection() -> bool:
    """Test connection to the PostgreSQL database."""
    settings = get_settings()
    
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.begin() as conn:
            # Simple connectivity test
            result = await conn.execute(text("SELECT 1"))
            row = result.fetchone()  # This is not async
            assert row is not None
        
        await engine.dispose()
        logger.info("Database connection test successful", database="postgres")
        return True
        
    except SQLAlchemyError as e:
        logger.error(
            "Database connection test failed",
            database="postgres",
            error=str(e)
        )
        return False
    except Exception as e:
        logger.error(
            "Unexpected error during database connection test",
            database="postgres", 
            error=str(e)
        )
        return False


def ensure_database(**kwargs) -> bool:
    """
    Ensure database connectivity (PostgreSQL version).
    
    Note: For PostgreSQL, we assume the database already exists (created via docker-compose
    or deployment scripts). This function only tests connectivity.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    logger.info("Testing PostgreSQL database connectivity...")
    return asyncio.run(test_database_connection())