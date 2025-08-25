"""Tests for database bootstrap functionality."""

import pytest
from unittest.mock import patch, MagicMock

from app.db.bootstrap import _build_master_connection_string, _database_exists, ensure_database


def test_build_master_connection_string():
    """Test master database connection string building."""
    conn_str = _build_master_connection_string()
    
    # Check that it contains expected components
    assert "DRIVER={ODBC Driver 18 for SQL Server}" in conn_str
    assert "DATABASE=master" in conn_str
    assert "TrustServerCertificate=yes" in conn_str


def test_database_exists_true():
    """Test database exists check when database is found."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)
    
    result = _database_exists(mock_conn, "TestDB")
    
    assert result is True
    mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM sys.databases WHERE name = ?", ("TestDB",))


def test_database_exists_false():
    """Test database exists check when database is not found."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (0,)
    
    result = _database_exists(mock_conn, "TestDB")
    
    assert result is False


@patch('app.db.bootstrap.pyodbc.connect')
@patch('app.db.bootstrap._database_exists')
def test_ensure_database_skip_creation(mock_db_exists, mock_connect):
    """Test ensure_database with skip_creation=True."""
    result = ensure_database(skip_creation=True)
    
    assert result is True
    mock_connect.assert_not_called()
    mock_db_exists.assert_not_called()


@patch('app.db.bootstrap.pyodbc.connect')
@patch('app.db.bootstrap._database_exists')
def test_ensure_database_already_exists(mock_db_exists, mock_connect):
    """Test ensure_database when database already exists."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_db_exists.return_value = True
    
    result = ensure_database(max_attempts=1)
    
    assert result is True
    mock_connect.assert_called_once()
    mock_db_exists.assert_called_once_with(mock_conn, "WeatherAI")


@patch('app.db.bootstrap.pyodbc.connect')
@patch('app.db.bootstrap._database_exists')
@patch('app.db.bootstrap._create_database')
def test_ensure_database_creates_new(mock_create_db, mock_db_exists, mock_connect):
    """Test ensure_database when database needs to be created."""
    mock_conn = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    # First call: database doesn't exist, second call: database exists after creation
    mock_db_exists.side_effect = [False, True]
    
    result = ensure_database(max_attempts=1)
    
    assert result is True
    mock_create_db.assert_called_once_with(mock_conn, "WeatherAI")
    assert mock_db_exists.call_count == 2


@patch('app.db.bootstrap.pyodbc.connect')
def test_ensure_database_connection_fails(mock_connect):
    """Test ensure_database when connection fails."""
    import pyodbc
    mock_connect.side_effect = pyodbc.Error("Connection failed")
    
    result = ensure_database(max_attempts=1, sleep_seconds=0)
    
    assert result is False
    mock_connect.assert_called_once()