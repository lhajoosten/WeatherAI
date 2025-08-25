"""Database bootstrap utilities for ensuring WeatherAI database exists."""

import logging
import time
from typing import Any

import pyodbc

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_master_connection_string() -> str:
    """Build a connection string for connecting to the master database."""
    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.db_server},{settings.db_port};"
        f"DATABASE=master;"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate=yes;"
    )


def _database_exists(conn: pyodbc.Connection, db_name: str) -> bool:
    """Check if database exists."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM sys.databases WHERE name = ?", 
            (db_name,)
        )
        result = cursor.fetchone()
        return result[0] > 0 if result else False
    finally:
        cursor.close()


def _create_database(conn: pyodbc.Connection, db_name: str) -> None:
    """Create database using CREATE DATABASE statement."""
    cursor = conn.cursor()
    try:
        # CREATE DATABASE must be executed outside of a transaction
        # Use quoted identifier to handle database names with special characters
        cursor.execute(f"CREATE DATABASE [{db_name}]")
        cursor.commit()
        logger.info(f"Successfully created database: {db_name}")
    finally:
        cursor.close()


def ensure_database(
    max_attempts: int = 30,
    sleep_seconds: int = 2,
    skip_creation: bool = False
) -> bool:
    """
    Ensure the WeatherAI database exists, creating it if necessary.
    
    Args:
        max_attempts: Maximum number of connection attempts
        sleep_seconds: Seconds to wait between attempts
        skip_creation: If True, skip database creation (useful for external DB management)
        
    Returns:
        bool: True if database is available, False otherwise
    """
    if skip_creation:
        logger.info("Database bootstrap skipped (SKIP_DB_BOOTSTRAP=true)")
        return True
        
    db_name = settings.db_name
    master_conn_str = _build_master_connection_string()
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                f"Database bootstrap attempt {attempt}/{max_attempts}: "
                f"Connecting to master database on {settings.db_server}:{settings.db_port}"
            )
            
            # Connect with autocommit=True to avoid transaction issues with CREATE DATABASE
            with pyodbc.connect(master_conn_str, autocommit=True) as conn:
                logger.debug("Connected to master database successfully")
                
                if _database_exists(conn, db_name):
                    logger.info(f"Database '{db_name}' already exists")
                    return True
                
                logger.info(f"Database '{db_name}' does not exist, creating it...")
                _create_database(conn, db_name)
                
                # Verify creation
                if _database_exists(conn, db_name):
                    logger.info(f"Database '{db_name}' created successfully")
                    return True
                else:
                    logger.error(f"Database '{db_name}' creation verification failed")
                    
        except pyodbc.Error as e:
            error_msg = str(e)
            logger.warning(
                f"Database bootstrap attempt {attempt}/{max_attempts} failed: {error_msg}"
            )
            
            # Handle specific SQL Server errors
            if "Login failed" in error_msg:
                logger.error("Authentication failed - check DB_USER and DB_PASSWORD")
            elif "server was not found" in error_msg or "Cannot open server" in error_msg:
                logger.warning(f"Server not reachable - retrying in {sleep_seconds} seconds...")
            elif "error 40" in error_msg:  # Network-related errors
                logger.warning(f"Network error - retrying in {sleep_seconds} seconds...")
            
            if attempt < max_attempts:
                time.sleep(sleep_seconds)
            else:
                logger.error(
                    f"Database bootstrap failed after {max_attempts} attempts. "
                    f"Please check: 1) SQL Server is running, 2) Network connectivity, "
                    f"3) Authentication credentials, 4) Server allows remote connections"
                )
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error during database bootstrap: {e}")
            if attempt < max_attempts:
                time.sleep(sleep_seconds)
            else:
                return False
    
    return False