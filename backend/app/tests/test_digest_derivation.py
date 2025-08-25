"""Tests for digest derivation functions."""

import pytest
from app.services.forecast_derivation import (
    compute_temp_range,
    find_peak_rain_window,
    find_lowest_wind_window,
    compute_comfort_score,
    generate_activity_blocks,
    derive_all_metrics
)


class TestDerivationFunctions:
    """Test forecast derivation functions with synthetic data."""
    
    def test_compute_temp_range_basic(self):
        """Test basic temperature range computation."""
        hourly_data = [
            {"temperature": 15.0},
            {"temperature": 20.0},
            {"temperature": 18.0},
            {"temperature": 12.0}
        ]
        
        temp_min, temp_max = compute_temp_range(hourly_data)
        assert temp_min == 12.0
        assert temp_max == 20.0
    
    def test_compute_temp_range_empty(self):
        """Test temperature range with empty data."""
        with pytest.raises(ValueError, match="No hourly data provided"):
            compute_temp_range([])
    
    def test_compute_temp_range_no_temperature(self):
        """Test temperature range with no valid temperature data."""
        hourly_data = [{"humidity": 50}, {"wind_speed": 10}]
        
        with pytest.raises(ValueError, match="No valid temperature data found"):
            compute_temp_range(hourly_data)
    
    def test_find_peak_rain_window_basic(self):
        """Test finding peak rain window."""
        hourly_data = [
            {"precipitation": 0.0},
            {"precipitation": 0.5},
            {"precipitation": 2.0},  # Peak hour
            {"precipitation": 1.0},
            {"precipitation": 0.0}
        ]
        
        window = find_peak_rain_window(hourly_data)
        assert window is not None
        assert window.start_hour == 2
        assert window.end_hour == 2
        assert window.duration_hours == 1
    
    def test_find_peak_rain_window_no_rain(self):
        """Test peak rain window with no significant rain."""
        hourly_data = [
            {"precipitation": 0.0},
            {"precipitation": 0.05},  # Below threshold
            {"precipitation": 0.0}
        ]
        
        window = find_peak_rain_window(hourly_data)
        assert window is None
    
    def test_find_lowest_wind_window_basic(self):
        """Test finding lowest wind window."""
        hourly_data = [
            {"wind_speed": 15.0},
            {"wind_speed": 5.0},   # Start of calm period
            {"wind_speed": 3.0},   # Calmest
            {"wind_speed": 20.0},
            {"wind_speed": 10.0}
        ]
        
        window = find_lowest_wind_window(hourly_data)
        assert window is not None
        assert window.start_hour == 1
        assert window.end_hour == 2
        assert window.duration_hours == 2
    
    def test_compute_comfort_score_optimal(self):
        """Test comfort score with optimal conditions."""
        score = compute_comfort_score(
            temp_min=19.0,
            temp_max=23.0,
            total_precip=0.0,
            avg_wind=8.0,
            avg_humidity=50.0
        )
        
        # Should be high score for optimal conditions
        assert score > 0.9
    
    def test_compute_comfort_score_challenging(self):
        """Test comfort score with challenging conditions."""
        score = compute_comfort_score(
            temp_min=5.0,   # Cold
            temp_max=8.0,
            total_precip=15.0,  # Heavy rain
            avg_wind=35.0,  # Very windy
            avg_humidity=85.0   # High humidity
        )
        
        # Should be low score for challenging conditions
        assert score < 0.3
    
    def test_generate_activity_blocks_basic(self):
        """Test activity block generation."""
        # Create 24 hours of mild weather
        hourly_data = []
        for hour in range(24):
            hourly_data.append({
                "temperature": 20.0,
                "precipitation": 0.0,
                "wind_speed": 10.0,
                "humidity": 50.0
            })
        
        preferences = {
            "outdoor_activities": True,
            "temperature_tolerance": "normal",
            "rain_tolerance": "low"
        }
        
        blocks = generate_activity_blocks(hourly_data, preferences)
        
        # Should generate 3 blocks (morning, afternoon, evening)
        assert len(blocks) == 3
        
        # Check block structure
        for block in blocks:
            assert block.activity_type in ["indoor", "outdoor", "mixed"]
            assert 0 <= block.suitability_score <= 1.0
            assert block.time_window.duration_hours > 0
    
    def test_derive_all_metrics_integration(self):
        """Test integration of all derivation functions."""
        # Create synthetic 24-hour forecast
        hourly_data = []
        for hour in range(24):
            temp = 15.0 + 5.0 * (1 + 0.8 * (hour - 12) / 12) if 6 <= hour <= 18 else 15.0
            precip = 2.0 if 14 <= hour <= 16 else 0.0
            wind = 5.0 + (10.0 if precip > 0 else 0.0)
            
            hourly_data.append({
                "temperature": temp,
                "precipitation": precip,
                "wind_speed": wind,
                "humidity": 60.0
            })
        
        preferences = {
            "outdoor_activities": True,
            "temperature_tolerance": "normal",
            "rain_tolerance": "low"
        }
        
        metrics = derive_all_metrics(hourly_data, preferences)
        
        # Validate all expected keys are present
        expected_keys = [
            "temp_min_c", "temp_max_c", "peak_rain_window",
            "lowest_wind_window", "comfort_score", "activity_blocks"
        ]
        for key in expected_keys:
            assert key in metrics
        
        # Validate data types and ranges
        assert isinstance(metrics["temp_min_c"], float)
        assert isinstance(metrics["temp_max_c"], float)
        assert metrics["temp_min_c"] <= metrics["temp_max_c"]
        assert 0.0 <= metrics["comfort_score"] <= 1.0
        assert isinstance(metrics["activity_blocks"], list)
        
        # Should find rain window during afternoon
        assert metrics["peak_rain_window"] is not None
        assert 14 <= metrics["peak_rain_window"].start_hour <= 16