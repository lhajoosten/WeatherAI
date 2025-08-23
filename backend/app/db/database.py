from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import settings
from app.db.models import Base
import logging

logger = logging.getLogger(__name__)

# Create async engine for MSSQL
# Note: pyodbc is synchronous but SQLAlchemy will wrap it in greenlets/threadpool
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


async def init_db():
    """Initialize database - create all tables.
    
    TODO: Replace with Alembic migrations in production.
    """
    logger.info("Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db():
    """Close database engine."""
    logger.info("Closing database connection...")
    await engine.dispose()
    logger.info("Database connection closed")