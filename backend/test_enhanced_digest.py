"""Test for enhanced Morning Digest functionality.

This test validates the full implementation of the Morning Digest feature
including real data integration, strict validation, and enhanced metrics.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.digest_service import DigestService
from app.services.digest_real_providers import DatabaseForecastProvider, DatabasePreferencesProvider
from app.metrics.digest import DigestMetrics, InstrumentedDigestService
from app.schemas.digest import DigestResponse, Bullet, Summary


class TestEnhancedDigestService:
    """Test enhanced digest service functionality."""

    def test_digest_metrics_derived_calculations(self):
        """Test enhanced metrics calculations."""
        metrics = DigestMetrics()
        
        # Test cache hit ratio calculation
        assert metrics.get_cache_hit_ratio() == 0.0
        
        # Add some cache events
        metrics.increment_counter("digest_cache_hit_count")
        metrics.increment_counter("digest_cache_hit_count")
        metrics.increment_counter("digest_cache_miss_count")
        
        # Should be 2/3 = 0.667
        ratio = metrics.get_cache_hit_ratio()
        assert abs(ratio - 0.6666666666666666) < 0.001
        
        # Test token usage tracking
        assert metrics.get_avg_tokens_per_digest() == 0.0
        
        metrics.record_token_usage(100)
        metrics.record_token_usage(200)
        metrics.record_token_usage(150)
        
        avg_tokens = metrics.get_avg_tokens_per_digest()
        assert avg_tokens == 150.0
        
        # Test daily opens tracking
        assert metrics.get_daily_digest_open_rate("2024-01-15") == 0.0
        
        metrics.record_digest_open("2024-01-15")
        metrics.record_digest_open("2024-01-15")
        
        assert metrics.get_daily_digest_open_rate("2024-01-15") == 2.0

    def test_instrumented_service_functionality(self):
        """Test instrumented service wrapper."""
        metrics = DigestMetrics()
        instrumented = InstrumentedDigestService(metrics)
        
        # Test token usage recording
        instrumented.record_token_usage(50, 75)
        assert metrics.get_avg_tokens_per_digest() == 125.0
        
        # Test digest access recording
        instrumented.record_digest_access("2024-01-15")
        assert metrics.get_daily_digest_open_rate("2024-01-15") == 1.0

    def test_summary_validation_and_enforcement(self):
        """Test strict summary format validation."""
        from app.services.digest_service import DigestService
        from app.services.digest_providers import PlaceholderForecastProvider, PlaceholderPreferencesProvider
        
        service = DigestService(
            PlaceholderForecastProvider(),
            PlaceholderPreferencesProvider(),
            use_llm=False
        )
        
        # Test with insufficient bullets
        summary_with_few_bullets = Summary(
            narrative="Test narrative",
            bullets=[
                Bullet(text="First bullet", category="weather", priority=1)
            ],
            driver="Test driver"
        )
        
        validated = service._validate_and_enforce_summary_format(summary_with_few_bullets)
        
        # Should have exactly 3 bullets
        assert len(validated.bullets) == 3
        assert validated.bullets[0].text == "First bullet"
        assert validated.bullets[1].text == "Weather conditions require attention - stay informed and plan accordingly"
        
        # Test bullet priority enforcement
        assert all(1 <= bullet.priority <= 3 for bullet in validated.bullets)
        
        # Test narrative trimming
        long_narrative = "x" * 400
        summary_with_long_narrative = Summary(
            narrative=long_narrative,
            bullets=[
                Bullet(text="Bullet 1", category="weather", priority=1),
                Bullet(text="Bullet 2", category="weather", priority=2),
                Bullet(text="Bullet 3", category="weather", priority=3)
            ],
            driver="Test driver"
        )
        
        validated_long = service._validate_and_enforce_summary_format(summary_with_long_narrative)
        assert len(validated_long.narrative) <= 300
        assert validated_long.narrative.endswith("...")

    def test_token_estimation_and_trimming(self):
        """Test token budget enforcement utilities."""
        from app.services.digest_service import DigestService
        from app.services.digest_providers import PlaceholderForecastProvider, PlaceholderPreferencesProvider
        
        service = DigestService(
            PlaceholderForecastProvider(),
            PlaceholderPreferencesProvider(),
            use_llm=False
        )
        
        # Test token estimation
        short_text = "Hello world"
        tokens = service._estimate_token_count(short_text)
        assert tokens == len(short_text) // 4
        
        # Test prompt trimming
        long_prompt = "x" * 1000
        max_tokens = 50  # 200 chars max
        trimmed = service._trim_prompt_to_budget(long_prompt, max_tokens)
        
        # Should be trimmed
        assert len(trimmed) < len(long_prompt)
        assert "...[trimmed]..." in trimmed

    @pytest.mark.asyncio
    async def test_digest_service_with_mock_providers(self):
        """Test digest service with mocked real providers."""
        # Mock database session
        mock_session = AsyncMock()
        
        # Mock forecast provider
        mock_forecast_provider = AsyncMock()
        mock_forecast_provider.get_forecast.return_value = {
            "location_id": 1,
            "date": "2024-01-15",
            "last_updated": "2024-01-15T12:00:00",
            "hourly": [
                {
                    "time": f"2024-01-15T{hour:02d}:00:00",
                    "temperature": 20.0 + hour,
                    "precipitation": 0.0,
                    "wind_speed": 10.0,
                    "humidity": 60.0
                }
                for hour in range(24)
            ]
        }
        
        # Mock preferences provider
        mock_preferences_provider = AsyncMock()
        mock_preferences_provider.get_preferences.return_value = {
            "outdoor_activities": True,
            "temperature_tolerance": "normal",
            "rain_tolerance": "low",
            "units_system": "metric",
            "time_zone": "UTC",
            "activity_preferences": ["walking", "cycling"]
        }
        
        # Mock location service
        mock_location_service = AsyncMock()
        mock_location_service.get_user_primary_location.return_value = 1
        
        # Create service without LLM for testing
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            location_service=mock_location_service,
            use_llm=False
        )
        
        # Test digest generation
        digest = await service.get_morning_digest(user_id="123", date="2024-01-15")
        
        # Validate response structure
        assert isinstance(digest, DigestResponse)
        assert digest.date == "2024-01-15"
        assert digest.user_id == "123"
        assert digest.location_id == 1
        
        # Validate summary has exactly 3 bullets
        assert len(digest.summary.bullets) == 3
        
        # Validate derived metrics are present
        assert digest.derived.temp_min_c is not None
        assert digest.derived.temp_max_c is not None
        assert digest.derived.comfort_score is not None
        
        # Validate cache metadata
        assert digest.cache_meta.hit is False
        assert digest.cache_meta.ttl_seconds == 600  # 10 minutes
        
        # Validate no token metadata for placeholder mode
        assert digest.tokens_meta is None

    def test_all_metrics_structure(self):
        """Test the complete metrics structure includes all required fields."""
        metrics = DigestMetrics()
        
        # Add some test data
        metrics.increment_counter("digest_generation_success_count")
        metrics.increment_counter("digest_cache_hit_count")
        metrics.record_token_usage(150)
        metrics.record_digest_open("2024-01-15")
        
        all_metrics = metrics.get_all_metrics()
        
        # Validate structure
        assert "counters" in all_metrics
        assert "histograms" in all_metrics
        assert "derived" in all_metrics
        
        # Validate derived metrics include all required fields from issue #14
        derived = all_metrics["derived"]
        assert "digest_cache_hit_ratio" in derived
        assert "avg_tokens_per_digest" in derived
        assert "daily_digest_open_rate" in derived
        assert "total_digest_opens" in derived
        
        # Validate values
        assert derived["avg_tokens_per_digest"] == 150.0
        assert derived["total_digest_opens"] == 1.0


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestEnhancedDigestService()
    
    print("🧪 Running enhanced digest tests...")
    
    try:
        test_instance.test_digest_metrics_derived_calculations()
        print("✅ Digest metrics calculations work")
        
        test_instance.test_instrumented_service_functionality()
        print("✅ Instrumented service functionality works")
        
        test_instance.test_summary_validation_and_enforcement()
        print("✅ Summary validation and enforcement works")
        
        test_instance.test_token_estimation_and_trimming()
        print("✅ Token budget enforcement works")
        
        test_instance.test_all_metrics_structure()
        print("✅ Complete metrics structure works")
        
        print("\n🎉 All enhanced digest tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()