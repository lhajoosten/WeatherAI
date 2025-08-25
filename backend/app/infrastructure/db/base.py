"""Base repository patterns and Unit of Work implementation."""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar, Generic, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.database import get_db

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
        self._repositories: Dict[str, Any] = {}
    
    async def __aenter__(self) -> 'UnitOfWork':
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()
    
    async def rollback(self) -> None:
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