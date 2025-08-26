"""Unit tests for Unit of Work pattern."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict


# Define a minimal UnitOfWork for testing (avoiding full module import)
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
    
    def get_repository(self, repository_class: type) -> Any:
        """Get or create a repository instance."""
        repo_name = repository_class.__name__
        if repo_name not in self._repositories:
            self._repositories[repo_name] = repository_class(self.session)
        return self._repositories[repo_name]


# Minimal repository for testing
class MockRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture  
def uow(mock_session):
    """Unit of Work instance with mock session."""
    return UnitOfWork(mock_session)


@pytest.mark.asyncio
async def test_uow_commit_on_success(uow, mock_session):
    """Test UoW commits transaction on successful completion."""
    async with uow:
        pass  # Successful operation
    
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_uow_rollback_on_exception(uow, mock_session):
    """Test UoW rolls back transaction on exception."""
    with pytest.raises(ValueError):
        async with uow:
            raise ValueError("Test error")
    
    mock_session.rollback.assert_called_once()
    mock_session.commit.assert_not_called()


@pytest.mark.asyncio
async def test_uow_get_repository(uow, mock_session):
    """Test UoW creates and caches repository instances."""
    # First call should create new repository
    repo1 = uow.get_repository(MockRepository)
    assert isinstance(repo1, MockRepository)
    assert repo1.session is mock_session
    
    # Second call should return cached instance
    repo2 = uow.get_repository(MockRepository)
    assert repo1 is repo2


@pytest.mark.asyncio  
async def test_uow_manual_commit(uow, mock_session):
    """Test manual commit operation."""
    await uow.commit()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_uow_manual_rollback(uow, mock_session):
    """Test manual rollback operation."""
    await uow.rollback()
    mock_session.rollback.assert_called_once()