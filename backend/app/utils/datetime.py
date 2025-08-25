"""DateTime utilities for WeatherAI backend."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Get current UTC datetime.

    Returns:
        Current datetime in UTC timezone.
    """
    return datetime.now(UTC)
