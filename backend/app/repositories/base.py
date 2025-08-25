"""Base repository patterns and Unit of Work implementation."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db

# Type variable for repository types
TRepository = TypeVar('TRepository')


class BaseRepository(ABC):
    """Abstract base repository with common patterns."""
    
    def __init__(self, session: AsyncSession):
        self.session = session


class UnitOfWork:
    """Unit of Work pattern for managing database transactions."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repositories: dict = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
    
    async def commit(self):
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self):
        """Rollback the current transaction."""
        await self.session.rollback()
    
    def get_repository(self, repository_class: type[TRepository]) -> TRepository:
        """Get or create a repository instance."""
        repo_name = repository_class.__name__
        if repo_name not in self._repositories:
            self._repositories[repo_name] = repository_class(self.session)
        return self._repositories[repo_name]


@asynccontextmanager
async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    """Get a Unit of Work instance with database session."""
    async for session in get_db():
        uow = UnitOfWork(session)
        try:
            yield uow
        finally:
            await session.close()