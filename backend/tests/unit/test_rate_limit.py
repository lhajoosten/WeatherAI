"""Tests for streaming rate limiting - Phase 4."""

import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.ai.rag.streaming_rate_limit import (
    StreamingRateLimiter,
    check_streaming_rate_limit
)
from app.domain.exceptions import RateLimitExceededError
from app.core.constants import CachePrefix


class TestStreamingRateLimiter:
    """Test streaming rate limiter functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = MagicMock()
        settings.rag_stream_rate_limit = 20
        settings.rag_stream_rate_window_seconds = 300  # 5 minutes
        return settings
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock Redis client."""
        redis_mock = AsyncMock()
        redis_mock.is_connected = True
        return redis_mock
    
    @pytest.fixture
    def rate_limiter(self, mock_settings):
        """Create rate limiter with mocked settings."""
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.get_settings', return_value=mock_settings):
            return StreamingRateLimiter()
    
    def test_redis_key_generation(self, rate_limiter):
        """Test Redis key generation for different users."""
        
        # Authenticated user
        key_auth = rate_limiter._get_redis_key("user123")
        assert key_auth == f"{CachePrefix.RATE_LIMIT_STREAM}:user_user123"
        
        # Anonymous user
        key_anon = rate_limiter._get_redis_key(None)
        assert key_anon == f"{CachePrefix.RATE_LIMIT_STREAM}:anonymous"
    
    @pytest.mark.asyncio
    async def test_rate_limit_within_limits(self, rate_limiter, mock_redis_client):
        """Test rate limiting when within limits."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client', mock_redis_client):
            # Mock pipeline operations
            pipeline_mock = AsyncMock()
            pipeline_mock.execute.return_value = [None, 5]  # 5 requests in window
            mock_redis_client.pipeline.return_value.__aenter__.return_value = pipeline_mock
            
            # Should pass since 5 < 20
            result = await rate_limiter.check_rate_limit("user123")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limiter, mock_redis_client):
        """Test rate limiting when limit is exceeded."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client', mock_redis_client):
            # Mock pipeline operations
            pipeline_mock = AsyncMock()
            pipeline_mock.execute.return_value = [None, 21]  # 21 requests in window (exceeds limit of 20)
            mock_redis_client.pipeline.return_value.__aenter__.return_value = pipeline_mock
            
            # Should raise rate limit error
            with pytest.raises(RateLimitExceededError) as exc_info:
                await rate_limiter.check_rate_limit("user123")
            
            assert exc_info.value.limit == 20
            assert exc_info.value.window_seconds == 300
            assert exc_info.value.endpoint == "rag_stream"
    
    @pytest.mark.asyncio
    async def test_rate_limit_redis_unavailable(self, rate_limiter):
        """Test rate limiting when Redis is unavailable."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client') as mock_redis:
            mock_redis.is_connected = False
            
            # Should allow request when Redis is unavailable
            result = await rate_limiter.check_rate_limit("user123")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_anonymous_user(self, rate_limiter, mock_redis_client):
        """Test rate limiting for anonymous users."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client', mock_redis_client):
            # Mock pipeline operations
            pipeline_mock = AsyncMock()
            pipeline_mock.execute.return_value = [None, 10]  # 10 requests in window
            mock_redis_client.pipeline.return_value.__aenter__.return_value = pipeline_mock
            
            result = await rate_limiter.check_rate_limit(None)  # Anonymous user
            assert result is True
            
            # Verify correct key was used
            pipeline_mock.zcard.assert_called()
    
    @pytest.mark.asyncio
    async def test_rate_limit_window_cleanup(self, rate_limiter, mock_redis_client):
        """Test that expired entries are cleaned up."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client', mock_redis_client):
            # Mock pipeline operations
            pipeline_mock = AsyncMock()
            pipeline_mock.execute.return_value = [None, 5]
            mock_redis_client.pipeline.return_value.__aenter__.return_value = pipeline_mock
            
            await rate_limiter.check_rate_limit("user123")
            
            # Verify cleanup was called
            pipeline_mock.zremrangebyscore.assert_called_once()
            
            # Verify new entry was added
            mock_redis_client.zadd.assert_called_once()
            
            # Verify expiration was set
            mock_redis_client.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_rate_limit_exact_limit(self, rate_limiter, mock_redis_client):
        """Test rate limiting at exact limit boundary."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client', mock_redis_client):
            # Mock pipeline operations
            pipeline_mock = AsyncMock()
            pipeline_mock.execute.return_value = [None, 20]  # Exactly at limit
            mock_redis_client.pipeline.return_value.__aenter__.return_value = pipeline_mock
            
            # Should raise rate limit error (20 >= 20)
            with pytest.raises(RateLimitExceededError):
                await rate_limiter.check_rate_limit("user123")
    
    @pytest.mark.asyncio
    async def test_rate_limit_redis_error_fallback(self, rate_limiter, mock_redis_client):
        """Test fallback behavior when Redis operations fail."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client', mock_redis_client):
            # Mock Redis operation failure
            mock_redis_client.pipeline.side_effect = Exception("Redis error")
            
            # Should allow request on Redis error
            result = await rate_limiter.check_rate_limit("user123")
            assert result is True


class TestRateLimitConvenienceFunction:
    """Test convenience function for rate limiting."""
    
    @pytest.mark.asyncio
    async def test_check_streaming_rate_limit_pass(self):
        """Test convenience function when rate limit passes."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.streaming_rate_limiter') as mock_limiter:
            mock_limiter.check_rate_limit.return_value = True
            
            result = await check_streaming_rate_limit("user123")
            assert result is True
            
            mock_limiter.check_rate_limit.assert_called_once_with("user123")
    
    @pytest.mark.asyncio
    async def test_check_streaming_rate_limit_fail(self):
        """Test convenience function when rate limit fails."""
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.streaming_rate_limiter') as mock_limiter:
            mock_limiter.check_rate_limit.side_effect = RateLimitExceededError(20, 300, "rag_stream")
            
            with pytest.raises(RateLimitExceededError):
                await check_streaming_rate_limit("user123")


class TestRateLimitIntegration:
    """Integration tests for rate limiting scenarios."""
    
    @pytest.mark.asyncio
    async def test_multiple_users_isolation(self):
        """Test that rate limits are isolated per user."""
        
        mock_settings = MagicMock()
        mock_settings.rag_stream_rate_limit = 2  # Low limit for testing
        mock_settings.rag_stream_rate_window_seconds = 60
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.get_settings', return_value=mock_settings):
            rate_limiter = StreamingRateLimiter()
            
            with patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client') as mock_redis:
                mock_redis.is_connected = True
                
                # Mock different counts for different users
                def pipeline_side_effect():
                    pipeline_mock = AsyncMock()
                    
                    def execute_side_effect():
                        # Return different counts based on which key is being accessed
                        call_args = pipeline_mock.zcard.call_args
                        if call_args and "user_user1" in str(call_args):
                            return [None, 1]  # User1 has 1 request
                        elif call_args and "user_user2" in str(call_args):
                            return [None, 2]  # User2 has 2 requests (at limit)
                        return [None, 0]
                    
                    pipeline_mock.execute.side_effect = execute_side_effect
                    return pipeline_mock
                
                mock_redis.pipeline.return_value.__aenter__.side_effect = lambda: pipeline_side_effect()
                
                # User1 should pass (1 < 2)
                result1 = await rate_limiter.check_rate_limit("user1")
                assert result1 is True
                
                # User2 should fail (2 >= 2)
                with pytest.raises(RateLimitExceededError):
                    await rate_limiter.check_rate_limit("user2")
    
    @pytest.mark.asyncio
    async def test_time_window_behavior(self):
        """Test rate limiting behavior over time windows."""
        
        mock_settings = MagicMock()
        mock_settings.rag_stream_rate_limit = 3
        mock_settings.rag_stream_rate_window_seconds = 60  # 1 minute
        
        with patch('app.infrastructure.ai.rag.streaming_rate_limit.get_settings', return_value=mock_settings):
            rate_limiter = StreamingRateLimiter()
            
            # Mock time progression
            mock_time = 1000.0
            
            with patch('time.time', return_value=mock_time), \
                 patch('app.infrastructure.ai.rag.streaming_rate_limit.redis_client') as mock_redis:
                
                mock_redis.is_connected = True
                
                # Simulate cleanup of old entries and counting current ones
                pipeline_mock = AsyncMock()
                
                # First call: 2 requests in window
                pipeline_mock.execute.return_value = [None, 2]
                mock_redis.pipeline.return_value.__aenter__.return_value = pipeline_mock
                
                result = await rate_limiter.check_rate_limit("user123")
                assert result is True
                
                # Verify cleanup was called with correct time window
                cleanup_call = pipeline_mock.zremrangebyscore.call_args
                assert cleanup_call[0][1] == 0  # Start of range
                assert cleanup_call[0][2] == mock_time - 60  # End of range (window start)


if __name__ == "__main__":
    pytest.main([__file__])