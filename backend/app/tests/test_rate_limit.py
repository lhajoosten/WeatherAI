"""Tests for Redis rate limiting functionality."""

from unittest.mock import patch

import pytest

from app.services.rate_limit import RateLimitService


@pytest.mark.asyncio
async def test_in_memory_rate_limit_check():
    """Test in-memory rate limiting allows requests within limits."""
    service = RateLimitService()

    # First request should pass
    result = await service.check_rate_limit(user_id=1, endpoint="test")
    assert result is True

    # Check status
    status = await service.get_rate_limit_status(user_id=1, endpoint="test")
    assert status["current_count"] == 1
    assert status["remaining"] == 59  # Default is 60 per minute


@pytest.mark.asyncio
async def test_in_memory_rate_limit_exceeded():
    """Test in-memory rate limiting blocks requests when limit exceeded."""
    from datetime import datetime

    from fastapi import HTTPException

    service = RateLimitService()

    # Manually set up exceeded limit with real datetime objects
    now = datetime.utcnow()
    service._limits = {
        "user_1": {
            "test": [(now, 1) for _ in range(60)]  # Max for regular endpoint
        }
    }

    # Next request should raise HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await service.check_rate_limit(user_id=1, endpoint="test")

    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
@patch('app.services.rate_limit.is_redis_available')
async def test_redis_fallback_when_unavailable(mock_is_available):
    """Test Redis rate limiting falls back to in-memory when Redis unavailable."""
    mock_is_available.return_value = False

    service = RateLimitService()
    service.use_redis = False  # Force fallback mode

    # Should use fallback service
    result = await service.check_rate_limit(user_id=1, endpoint="test")
    assert result is True


@pytest.mark.asyncio
async def test_rate_limit_endpoint_specific_limits():
    """Test that different endpoints have different rate limits."""
    service = RateLimitService()

    # Test LLM endpoint has lower limit
    service._get_rate_limit("explain")
    regular_limit = service._get_rate_limit("regular")
    analytics_limit = service._get_rate_limit("analytics")

    # Note: These tests depend on the actual settings values
    # We're just testing that analytics gets 3x boost
    assert analytics_limit == regular_limit * 3
    # LLM endpoints use llm_requests_per_minute setting
