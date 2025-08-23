import logging
import urllib.parse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.models import Base

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
    """Initialize database using Alembic migrations.
    
    TODO: In production, run migrations separately during deployment.
    For development, this tries to upgrade to the latest revision.
    """
    logger.info("Running database migrations (alembic upgrade head)...")
    try:
        import os
        import subprocess

        # Change to the backend directory to run alembic
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            logger.info("Database migrations completed successfully")
        else:
            logger.error(f"Migration failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            # For development, fall back to manual table creation
            logger.warning("Falling back to create_all for development...")
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created via create_all")

    except Exception as exc:
        logger.exception("Failed to run migrations: %s", exc)
        # For development, fall back to manual table creation
        logger.warning("Falling back to create_all for development...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created via create_all")


async def close_db():
    """Close database engine."""
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed")
