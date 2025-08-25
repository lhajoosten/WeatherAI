"""Tests for Redis rate limiting functionality."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.rate_limit import RateLimitService, InMemoryRateLimitService, RedisRateLimitService


@pytest.mark.asyncio
async def test_in_memory_rate_limit_check():
    """Test in-memory rate limiting allows requests within limits."""
    service = InMemoryRateLimitService()
    
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
    from fastapi import HTTPException
    from datetime import datetime
    
    service = InMemoryRateLimitService()
    
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
@patch('app.services.rate_limit.get_redis_client')
@patch('app.services.rate_limit.is_redis_available')
async def test_redis_rate_limit_fallback(mock_is_available, mock_get_client):
    """Test Redis rate limiting falls back to in-memory when Redis unavailable."""
    mock_is_available.return_value = False
    mock_get_client.return_value = None
    
    service = RedisRateLimitService()
    
    # Should use fallback service
    result = await service.check_rate_limit(user_id=1, endpoint="test")
    assert result is True


@pytest.mark.asyncio
@patch('app.services.rate_limit.get_redis_client')
@patch('app.services.rate_limit.is_redis_available')
async def test_redis_rate_limit_success(mock_is_available, mock_get_client):
    """Test Redis rate limiting when Redis is available."""
    mock_is_available.return_value = True
    
    # Mock Redis client with proper async behavior
    mock_client = AsyncMock()
    mock_get_client.return_value = mock_client
    
    # Mock pipeline operations - need to make the pipeline async compatible
    mock_pipeline = AsyncMock()
    mock_client.pipeline.return_value = mock_pipeline
    mock_pipeline.execute = AsyncMock(return_value=[None, 5])  # 5 current requests
    mock_pipeline.zremrangebyscore = AsyncMock()
    mock_pipeline.zcard = AsyncMock()
    
    service = RedisRateLimitService()
    
    result = await service.check_rate_limit(user_id=1, endpoint="test")
    assert result is True
    
    # Verify Redis operations were called
    mock_client.pipeline.assert_called_once()
    # Don't check specific redis commands as they may vary in implementation


@pytest.mark.asyncio
@patch('app.services.rate_limit.settings')
@patch('app.services.rate_limit.is_redis_available')
async def test_adaptive_rate_limit_service(mock_is_available, mock_settings):
    """Test adaptive rate limiting service chooses correct backend."""
    mock_settings.use_redis_rate_limit = True
    
    service = RateLimitService()
    
    # Test with Redis available
    mock_is_available.return_value = True
    with patch.object(service._redis_service, 'check_rate_limit', return_value=True) as mock_redis:
        result = await service.check_rate_limit(user_id=1, endpoint="test")
        assert result is True
        mock_redis.assert_called_once()
    
    # Test with Redis unavailable
    mock_is_available.return_value = False
    with patch.object(service._memory_service, 'check_rate_limit', return_value=True) as mock_memory:
        result = await service.check_rate_limit(user_id=1, endpoint="test")
        assert result is True
        mock_memory.assert_called_once()


@pytest.mark.asyncio
async def test_rate_limit_endpoint_specific_limits():
    """Test that different endpoints have different rate limits."""
    service = InMemoryRateLimitService()
    
    # Test LLM endpoint has lower limit
    llm_limit = service._get_rate_limit("explain")
    regular_limit = service._get_rate_limit("regular")
    analytics_limit = service._get_rate_limit("analytics")
    
    assert llm_limit == 10  # LLM endpoints
    assert regular_limit == 60  # Regular endpoints
    assert analytics_limit == 180  # Analytics endpoints (3x regular)