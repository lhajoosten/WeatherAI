"""Tests for digest placeholder narrative generator."""

from app.application.dto.digest import Window
import pytest
try:
    from app.infrastructure.external.digest_placeholder import (  # type: ignore
        _build_narrative,
        _determine_weather_driver,
        _generate_bullets,
        build_placeholder_summary,
    )
except Exception:  # pragma: no cover
    pytest.skip("Legacy digest placeholder removed", allow_module_level=True)


class TestPlaceholderGenerator:
    """Test placeholder narrative generation functions."""

    def test_build_placeholder_summary_basic(self):
        """Test basic placeholder summary generation."""
        derived_metrics = {
            "temp_min_c": 18.0,
            "temp_max_c": 24.0,
            "comfort_score": 0.8,
            "activity_blocks": [],
            "peak_rain_window": None,
            "lowest_wind_window": None
        }

        preferences = {
            "outdoor_activities": True,
            "temperature_tolerance": "normal"
        }

        summary = build_placeholder_summary(derived_metrics, preferences)

        # Should return exactly 3 bullets as specified
        assert len(summary.bullets) == 3

        # Should have non-empty narrative and driver
        assert len(summary.narrative) > 0
        assert len(summary.driver) > 0

        # All bullets should have valid categories and priorities
        valid_categories = {"weather", "activity", "alert"}
        valid_priorities = {1, 2, 3}

        for bullet in summary.bullets:
            assert bullet.category in valid_categories
            assert bullet.priority in valid_priorities
            assert len(bullet.text) > 0

    def test_build_placeholder_summary_with_rain(self):
        """Test placeholder summary with rain conditions."""
        derived_metrics = {
            "temp_min_c": 15.0,
            "temp_max_c": 20.0,
            "comfort_score": 0.4,
            "activity_blocks": [],
            "peak_rain_window": Window(start_hour=14, end_hour=16, duration_hours=3),
            "lowest_wind_window": None
        }

        preferences = {"outdoor_activities": True}

        summary = build_placeholder_summary(derived_metrics, preferences)

        # Driver should be precipitation-related
        assert "precipitation" in summary.driver

        # Should include rain-related bullet
        rain_bullets = [b for b in summary.bullets if "rain" in b.text.lower()]
        assert len(rain_bullets) > 0

    def test_determine_weather_driver_precipitation(self):
        """Test weather driver determination with rain."""
        metrics = {
            "peak_rain_window": Window(start_hour=10, end_hour=12, duration_hours=3),
            "comfort_score": 0.7,
            "temp_max_c": 22,
            "temp_min_c": 18
        }

        driver = _determine_weather_driver(metrics)
        assert driver == "precipitation"

    def test_determine_weather_driver_temperature_extremes(self):
        """Test weather driver determination with extreme temperatures."""
        metrics_hot = {
            "peak_rain_window": None,
            "comfort_score": 0.7,
            "temp_max_c": 35,  # Hot
            "temp_min_c": 25
        }

        driver = _determine_weather_driver(metrics_hot)
        assert driver == "temperature extremes"

        metrics_cold = {
            "peak_rain_window": None,
            "comfort_score": 0.7,
            "temp_max_c": 8,
            "temp_min_c": 2  # Cold
        }

        driver = _determine_weather_driver(metrics_cold)
        assert driver == "temperature extremes"

    def test_determine_weather_driver_favorable(self):
        """Test weather driver determination with favorable conditions."""
        metrics = {
            "peak_rain_window": None,
            "comfort_score": 0.9,  # High comfort
            "temp_max_c": 22,
            "temp_min_c": 18
        }

        driver = _determine_weather_driver(metrics)
        assert driver == "favorable weather conditions"

    def test_build_narrative_variations(self):
        """Test narrative building with different conditions."""
        # Test precipitation narrative
        narrative = _build_narrative(15, 20, 0.6, "precipitation")
        assert "rainfall" in narrative.lower()
        assert "15°C to 20°C" in narrative

        # Test hot weather narrative
        narrative = _build_narrative(25, 35, 0.4, "temperature extremes")
        assert "hot" in narrative.lower()
        assert "35°C" in narrative

        # Test cold weather narrative
        narrative = _build_narrative(0, 8, 0.4, "temperature extremes")
        assert "cold" in narrative.lower()
        assert "0°C" in narrative

        # Test favorable conditions narrative
        narrative = _build_narrative(18, 24, 0.9, "favorable weather conditions")
        assert "excellent" in narrative.lower() or "perfect" in narrative.lower()

    def test_generate_bullets_count(self):
        """Test that exactly 3 bullets are always generated."""
        test_cases = [
            # Basic case
            {
                "derived_metrics": {
                    "temp_min_c": 20, "temp_max_c": 25, "peak_rain_window": None,
                    "lowest_wind_window": None, "comfort_score": 0.7
                },
                "activity_blocks": [],
                "preferences": {}
            },
            # With rain
            {
                "derived_metrics": {
                    "temp_min_c": 15, "temp_max_c": 20,
                    "peak_rain_window": Window(start_hour=14, end_hour=16, duration_hours=3),
                    "lowest_wind_window": None, "comfort_score": 0.4
                },
                "activity_blocks": [],
                "preferences": {}
            },
            # Extreme temperatures
            {
                "derived_metrics": {
                    "temp_min_c": 35, "temp_max_c": 40, "peak_rain_window": None,
                    "lowest_wind_window": None, "comfort_score": 0.2
                },
                "activity_blocks": [],
                "preferences": {}
            }
        ]

        for case in test_cases:
            bullets = _generate_bullets(
                case["derived_metrics"],
                case["activity_blocks"],
                case["preferences"]
            )
            assert len(bullets) == 3, f"Expected 3 bullets, got {len(bullets)}"

    def test_generate_bullets_temperature_references(self):
        """Test that bullets reference temperature values correctly."""
        derived_metrics = {
            "temp_min_c": 30.0,  # Hot
            "temp_max_c": 35.0,
            "peak_rain_window": None,
            "lowest_wind_window": None,
            "comfort_score": 0.3
        }

        bullets = _generate_bullets(derived_metrics, [], {})

        # First bullet should be temperature-focused and mention the high temp
        temp_bullet = bullets[0]
        assert temp_bullet.category == "weather"
        assert "35" in temp_bullet.text or "30" in temp_bullet.text
