"""Central datetime utilities for consistent timezone handling."""
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def parse_iso_utc(value: str | datetime) -> datetime:
    """Parse ISO timestamp to timezone-aware UTC datetime.
    
    This ensures consistent timezone handling across all providers and eliminates 
    naive vs aware datetime comparison errors.
    
    Args:
        value: ISO timestamp string or datetime object
        
    Returns:
        Timezone-aware datetime in UTC
        
    Raises:
        ValueError: If the timestamp cannot be parsed
    """
    if isinstance(value, datetime):
        # If already a datetime, ensure it's timezone-aware in UTC
        if value.tzinfo is None:
            # Assume naive datetime is UTC
            logger.debug(f"Converting naive datetime {value} to UTC")
            return value.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC if not already
            return value.astimezone(timezone.utc)
    
    if isinstance(value, str):
        try:
            # Handle common ISO formats
            if value.endswith('Z'):
                # Replace Z with explicit UTC offset
                value = value.replace('Z', '+00:00')
            
            # Parse ISO format with timezone
            dt = datetime.fromisoformat(value)
            
            # Ensure timezone-aware
            if dt.tzinfo is None:
                logger.debug(f"Parsed naive datetime {dt} from {value}, assuming UTC")
                return dt.replace(tzinfo=timezone.utc)
            else:
                # Convert to UTC
                return dt.astimezone(timezone.utc)
                
        except ValueError as e:
            logger.error(f"Failed to parse datetime string '{value}': {e}")
            raise ValueError(f"Invalid datetime format: {value}") from e
    
    raise ValueError(f"Unsupported datetime type: {type(value)}")


def truncate_error_message(error_msg: str, max_length: int = 500) -> str:
    """Truncate error message to prevent oversized database rows.
    
    Args:
        error_msg: The error message to truncate
        max_length: Maximum allowed length (default 500 chars)
        
    Returns:
        Truncated error message with ellipsis if needed
    """
    if len(error_msg) <= max_length:
        return error_msg
    
    return error_msg[:max_length - 3] + "..."