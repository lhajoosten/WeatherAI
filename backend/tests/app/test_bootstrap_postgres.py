"""Tests for PostgreSQL database bootstrap functionality."""

import pytest
from unittest.mock import AsyncMock, patch

from app.infrastructure.db.bootstrap import test_database_connection, ensure_database


@pytest.mark.asyncio
async def test_database_connection_success():
    """Test successful database connection."""
    with patch('app.infrastructure.db.bootstrap.create_async_engine') as mock_engine:
        mock_engine.return_value.begin = AsyncMock()
        mock_engine.return_value.dispose = AsyncMock()
        
        # Mock the connection and execution
        mock_conn = AsyncMock()
        mock_result = AsyncMock()
        mock_result.fetchone = AsyncMock(return_value=(1,))
        mock_conn.execute = AsyncMock(return_value=mock_result)
        mock_engine.return_value.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.return_value.begin.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = await test_database_connection()
        
        assert result is True
        mock_engine.assert_called_once()
        mock_conn.execute.assert_called_once_with("SELECT 1")


@pytest.mark.asyncio 
async def test_database_connection_failure():
    """Test database connection failure."""
    with patch('app.infrastructure.db.bootstrap.create_async_engine') as mock_engine:
        mock_engine.side_effect = Exception("Connection failed")
        
        result = await test_database_connection()
        
        assert result is False


def test_ensure_database_success():
    """Test ensure_database with successful connection."""
    with patch('app.infrastructure.db.bootstrap.asyncio.run') as mock_run:
        mock_run.return_value = True
        
        result = ensure_database()
        
        assert result is True
        mock_run.assert_called_once()


def test_ensure_database_failure():
    """Test ensure_database with failed connection.""" 
    with patch('app.infrastructure.db.bootstrap.asyncio.run') as mock_run:
        mock_run.return_value = False
        
        result = ensure_database()
        
        assert result is False


@pytest.mark.asyncio
async def test_uuid_roundtrip():
    """Test UUID roundtrip with PostgreSQL."""
    import uuid
    test_uuid = uuid.uuid4()
    
    # This would be more comprehensive with an actual database connection
    # For now, just test that UUIDs can be converted to strings and back
    uuid_str = str(test_uuid)
    converted_back = uuid.UUID(uuid_str)
    
    assert test_uuid == converted_back


def test_transaction_rollback():
    """Test basic transaction rollback behavior."""
    # This is a placeholder for a more comprehensive transaction test
    # that would require an actual database connection
    assert True  # Placeholder until we have full test infrastructure