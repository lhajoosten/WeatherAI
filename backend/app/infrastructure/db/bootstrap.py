"""Database bootstrap functionality for PostgreSQL.

Note: PostgreSQL databases are typically created via docker-compose or deployment scripts.
This module provides basic connectivity testing.
"""

import logging
import structlog
import asyncio
import time
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from app.core.settings import get_settings

logger = structlog.get_logger(__name__)
std_logger = logging.getLogger(__name__)


async def test_database_connection() -> bool:
    """Test connection to the PostgreSQL database."""
    settings = get_settings()
    try:
        engine = create_async_engine(settings.database_url, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        logger.info("Database connection test successful", database="postgres")
        return True
    except SQLAlchemyError as e:  # pragma: no cover - error path
        logger.warning(
            "Database connection test failed",
            database="postgres",
            error=str(e)
        )
        return False
    except Exception as e:  # pragma: no cover - unexpected
        logger.error(
            "Unexpected error during database connection test",
            database="postgres",
            error=str(e)
        )
        return False


def ensure_database(
    max_attempts: Optional[int] = None,
    sleep_seconds: Optional[int] = None,
    skip_bootstrap: bool | None = None,
    **_: object,
) -> bool:
    """Attempt to verify database connectivity with retries.

    Args:
        max_attempts: Max attempts before giving up (falls back to settings)
        sleep_seconds: Seconds to sleep between attempts (falls back to settings)
        skip_bootstrap: If True, skip checks and return True

    Returns:
        True if connectivity confirmed, else False
    """
    settings = get_settings()
    if skip_bootstrap is None:
        skip_bootstrap = settings.skip_db_bootstrap
    if skip_bootstrap:
        logger.info("Skipping DB bootstrap per configuration", skip_bootstrap=skip_bootstrap)
        return True

    attempts = max_attempts or settings.db_bootstrap_max_attempts
    delay = sleep_seconds or settings.db_bootstrap_sleep_seconds
    logger.info(
        "Starting PostgreSQL connectivity attempts",
        attempts=attempts,
        delay_seconds=delay,
        database=settings.postgres_db,
        host=settings.postgres_host,
        port=settings.postgres_port,
    )

    for attempt in range(1, attempts + 1):
        start = time.time()
        ok = asyncio.run(test_database_connection())
        duration = round((time.time() - start) * 1000)
        if ok:
            logger.info(
                "Database connectivity established",
                attempt=attempt,
                duration_ms=duration,
                status="success",
            )
            return True
        logger.warning(
            "Database not yet available",
            attempt=attempt,
            max_attempts=attempts,
            wait_seconds=delay,
            duration_ms=duration,
        )
        time.sleep(delay)

    logger.error(
        "Database connectivity failed after max attempts",
        attempts=attempts,
        database=settings.postgres_db,
        host=settings.postgres_host,
        port=settings.postgres_port,
    )
    return False