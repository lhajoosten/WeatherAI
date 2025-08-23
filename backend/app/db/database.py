from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.db.models import Base
import logging
import asyncio
import urllib.parse
from sqlalchemy import text, create_engine as create_sync_engine
from sqlalchemy.exc import OperationalError, ProgrammingError, DBAPIError

logger = logging.getLogger(__name__)

# Create async engine for MSSQL (engine remains module-global)
engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,  # Use NullPool for better compatibility with pyodbc
    echo=settings.debug,
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


async def init_db():
    """Initialize database - create all tables.

    If the target database does not exist, attempt to create it by connecting to master.
    This function will retry several times while SQL Server finishes startup.
    TODO: Replace with Alembic migrations in production.
    """
    logger.info("Creating database tables (init_db)...")
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
            return
        except DBAPIError as exc:
            # SQL Server returns 4060 when the database is missing / login failed for DB
            msg = str(exc.orig) if exc.orig is not None else str(exc)
            logger.warning("Database init attempt %d/%d failed: %s", attempt, max_attempts, msg)

            # If database is missing, try to create it using a sync connection to master
            if "Cannot open database" in msg or "4060" in msg:
                logger.info("Detected missing database '%s'. Attempting to create it in master.", settings.db_name)
                try:
                    master_url = _build_sync_master_url()
                    sync_engine = create_sync_engine(master_url, connect_args={"timeout": 10})
                    # Run SELECT DB_ID(...) first, then CREATE DATABASE in its own autocommit call.
                    with sync_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                        res = conn.execute(text("SELECT DB_ID(:name) AS id"), {"name": settings.db_name})
                        db_id = res.scalar()
                        if not db_id:
                            conn.execute(text(f"CREATE DATABASE [{settings.db_name}]"))
                    sync_engine.dispose()
                    logger.info("Database '%s' ensured/created. Retrying table creation.", settings.db_name)
                    # small pause before retry
                    await asyncio.sleep(1)
                    continue
                except Exception as create_exc:
                    logger.exception("Failed to create database '%s': %s", settings.db_name, create_exc)

            # If SQL Server is not ready yet, wait and retry
            if attempt == max_attempts:
                logger.error("Exceeded max DB init attempts (%d). Raising error.", max_attempts)
                raise
            wait_seconds = min(5 * attempt, 30)
            logger.info("Waiting %ds before retrying DB init (attempt %d/%d).", wait_seconds, attempt, max_attempts)
            await asyncio.sleep(wait_seconds)
        except Exception as exc:
            logger.exception("Unexpected error during init_db: %s", exc)
            raise


async def close_db():
    """Close database engine."""
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed")