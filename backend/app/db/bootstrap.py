"""Database bootstrap functionality for creating database if it doesn't exist."""

import logging
import time
import urllib.parse
from typing import Optional

import pyodbc
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)
std_logger = logging.getLogger(__name__)


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


def _get_pyodbc_connection_string() -> str:
    """Get direct pyodbc connection string for master database."""
    return (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={settings.db_server},{settings.db_port};"
        f"DATABASE=master;"
        f"UID={settings.db_user};"
        f"PWD={settings.db_password};"
        f"TrustServerCertificate=yes"
    )


def ensure_database(
    max_attempts: int = 30,
    sleep_seconds: int = 2,
    skip_bootstrap: bool = False
) -> bool:
    """
    Ensure the target database exists, creating it if necessary.
    
    Args:
        max_attempts: Maximum number of connection attempts
        sleep_seconds: Seconds to wait between attempts
        skip_bootstrap: If True, skip database creation but still test connection
        
    Returns:
        True if database exists/was created successfully, False otherwise
    """
    if skip_bootstrap:
        logger.info(
            "Database bootstrap skipped by configuration",
            action="bootstrap.ensure_database", 
            status="skipped",
            skip_bootstrap=True
        )
        return True
    
    logger.info(
        "Starting database bootstrap process",
        action="bootstrap.ensure_database",
        status="started",
        target_database=settings.db_name,
        server=settings.db_server,
        max_attempts=max_attempts
    )
    
    connection_string = _get_pyodbc_connection_string()
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Test server connectivity first
            logger.debug(
                "Testing server connectivity",
                action="bootstrap.ensure_database", 
                attempt=attempt,
                server=settings.db_server
            )
            
            conn = pyodbc.connect(connection_string, autocommit=True)
            
            try:
                cursor = conn.cursor()
                
                # Check if database exists
                cursor.execute(
                    "SELECT database_id FROM sys.databases WHERE name = ?", 
                    settings.db_name
                )
                db_exists = cursor.fetchone() is not None
                
                if db_exists:
                    logger.info(
                        "Target database already exists",
                        action="bootstrap.ensure_database",
                        status="exists",
                        database=settings.db_name
                    )
                    return True
                else:
                    # Create database
                    logger.info(
                        "Creating target database", 
                        action="bootstrap.ensure_database",
                        status="creating",
                        database=settings.db_name
                    )
                    
                    # Use parameterized query safely - SQL Server doesn't allow parameters for DB names
                    # but we control settings.db_name from our config
                    create_sql = f"CREATE DATABASE [{settings.db_name}]"
                    cursor.execute(create_sql)
                    
                    logger.info(
                        "Database created successfully",
                        action="bootstrap.ensure_database", 
                        status="created",
                        database=settings.db_name
                    )
                    return True
                    
            finally:
                conn.close()
                
        except pyodbc.OperationalError as e:
            error_msg = str(e)
            
            # Distinguish between different types of errors
            if "Login failed" in error_msg or "18456" in error_msg:
                logger.error(
                    "Database authentication failed",
                    action="bootstrap.ensure_database",
                    status="auth_error", 
                    attempt=attempt,
                    error=error_msg
                )
                # Auth errors won't be resolved by retrying
                return False
                
            elif "server was not found" in error_msg.lower() or "Name or service not known" in error_msg:
                logger.warning(
                    "Database server unreachable",
                    action="bootstrap.ensure_database",
                    status="server_unreachable",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error_msg
                )
                
            elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
                logger.info(
                    "Target database missing, will create on next attempt",
                    action="bootstrap.ensure_database",
                    status="database_missing", 
                    attempt=attempt,
                    database=settings.db_name
                )
                
            else:
                logger.warning(
                    "Database connection attempt failed",
                    action="bootstrap.ensure_database", 
                    status="connection_error",
                    attempt=attempt,
                    max_attempts=max_attempts,
                    error=error_msg
                )
            
            if attempt < max_attempts:
                logger.debug(
                    f"Retrying in {sleep_seconds} seconds",
                    action="bootstrap.ensure_database",
                    retry_in_seconds=sleep_seconds
                )
                time.sleep(sleep_seconds)
            
        except Exception as e:
            logger.error(
                "Unexpected error during database bootstrap",
                action="bootstrap.ensure_database",
                status="unexpected_error",
                attempt=attempt,
                error=str(e),
                exc_info=True
            )
            
            if attempt < max_attempts:
                time.sleep(sleep_seconds)
    
    logger.error(
        "Database bootstrap failed after all attempts",
        action="bootstrap.ensure_database",
        status="failed", 
        max_attempts=max_attempts,
        database=settings.db_name
    )
    return False


def test_database_connection() -> bool:
    """Test connection to the target database (not master)."""
    try:
        # Build connection string for target database
        odbc_params = {
            "DRIVER": "{ODBC Driver 18 for SQL Server}",
            "SERVER": f"{settings.db_server},{settings.db_port}",
            "DATABASE": settings.db_name,
            "UID": settings.db_user,
            "PWD": settings.db_password,
            "TrustServerCertificate": "yes",
        }
        
        connection_string = ";".join([f"{k}={v}" for k, v in odbc_params.items()])
        conn = pyodbc.connect(connection_string)
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            
            logger.info(
                "Target database connection test successful",
                action="bootstrap.test_connection",
                status="success",
                database=settings.db_name
            )
            return True
            
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(
            "Target database connection test failed",
            action="bootstrap.test_connection", 
            status="failed",
            database=settings.db_name,
            error=str(e)
        )
        return False