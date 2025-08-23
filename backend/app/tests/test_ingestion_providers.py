"""Tests for multi-provider ingestion system."""
import pytest
from datetime import datetime, date, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.ingest.providers.openmeteo_forecast import OpenMeteoForecastProvider
from app.ingest.providers.openmeteo_observation import OpenMeteoObservationProvider
from app.ingest.providers.openmeteo_air_quality import OpenMeteoAirQualityProvider
from app.ingest.astronomy_service import AstronomyComputationService


class TestOpenMeteoForecastProvider:
    """Test OpenMeteo forecast provider."""

    @pytest.mark.asyncio
    async def test_forecast_provider_normalization(self):
        """Test forecast data normalization."""
        provider = OpenMeteoForecastProvider()
        
        # Mock API response
        mock_response = {
            "hourly": {
                "time": ["2023-08-23T00:00:00Z", "2023-08-23T01:00:00Z"],
                "temperature_2m": [20.5, 21.0],
                "precipitation_probability": [10, 15],
                "wind_speed_10m": [3.5, 4.0]
            }
        }
        
        # Test normalization
        records = provider._normalize_forecast_data(1, mock_response)
        
        assert len(records) == 2
        assert records[0]["location_id"] == 1
        assert records[0]["temp_c"] == 20.5
        assert records[0]["precipitation_probability_pct"] == 10
        assert records[0]["wind_kph"] == pytest.approx(12.6, rel=1e-1)  # 3.5 m/s * 3.6
        assert records[0]["model_name"] == "openmeteo_v1"
        assert "raw_json" in records[0]

    @pytest.mark.asyncio
    async def test_forecast_provider_api_call(self):
        """Test forecast provider API call."""
        provider = OpenMeteoForecastProvider()
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "hourly": {
                "time": ["2023-08-23T00:00:00Z"],
                "temperature_2m": [20.5],
                "precipitation_probability": [10],
                "wind_speed_10m": [3.5]
            }
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            records = await provider.fetch_forecast(1, 40.7128, -74.0060)
            
            assert len(records) == 1
            assert records[0]["temp_c"] == 20.5


class TestOpenMeteoObservationProvider:
    """Test OpenMeteo observation provider."""

    @pytest.mark.asyncio
    async def test_observation_provider_normalization(self):
        """Test observation data normalization."""
        provider = OpenMeteoObservationProvider()
        
        # Mock API response
        mock_response = {
            "hourly": {
                "time": ["2023-08-23T00:00:00Z", "2023-08-23T01:00:00Z"],
                "temperature_2m": [18.5, 19.0],
                "wind_speed_10m": [2.5, 3.0],
                "relative_humidity_2m": [65, 70],
                "precipitation": [0.0, 0.5]
            }
        }
        
        # Test normalization
        records = provider._normalize_observation_data(1, mock_response, hours_back=24)
        
        assert len(records) == 2
        assert records[0]["location_id"] == 1
        assert records[0]["temp_c"] == 18.5
        assert records[0]["wind_kph"] == pytest.approx(9.0, rel=1e-1)  # 2.5 m/s * 3.6
        assert records[0]["humidity_pct"] == 65
        assert records[0]["precip_mm"] == 0.0
        assert records[0]["source"] == "openmeteo"


class TestOpenMeteoAirQualityProvider:
    """Test OpenMeteo air quality provider."""

    @pytest.mark.asyncio
    async def test_air_quality_provider_normalization(self):
        """Test air quality data normalization."""
        provider = OpenMeteoAirQualityProvider()
        
        # Mock API response
        mock_response = {
            "hourly": {
                "time": ["2023-08-23T00:00:00Z", "2023-08-23T01:00:00Z"],
                "pm10": [15.2, 16.5],
                "pm2_5": [8.1, 9.0],
                "ozone": [45.3, 47.8],
                "nitrogen_dioxide": [12.5, 13.2],
                "sulphur_dioxide": [2.1, 2.3],
                "alder_pollen": [5, 7],
                "birch_pollen": [10, 12],
                "grass_pollen": [25, 30],
                "ragweed_pollen": [3, 4]
            }
        }
        
        # Test normalization
        records = provider._normalize_air_quality_data(1, mock_response, hours_back=24)
        
        assert len(records) == 2
        assert records[0]["location_id"] == 1
        assert records[0]["pm10"] == 15.2
        assert records[0]["pm2_5"] == 8.1
        assert records[0]["ozone"] == 45.3
        assert records[0]["no2"] == 12.5
        assert records[0]["so2"] == 2.1
        assert records[0]["pollen_tree"] == 10  # Max of alder(5) and birch(10)
        assert records[0]["pollen_grass"] == 25
        assert records[0]["pollen_weed"] == 3
        assert records[0]["source"] == "openmeteo"


class TestAstronomyComputationService:
    """Test astronomy computation service."""

    def test_astronomy_computation(self):
        """Test astronomy data computation."""
        service = AstronomyComputationService()
        
        # Test for New York coordinates
        lat, lon = 40.7128, -74.0060
        test_date = date(2023, 8, 23)
        
        result = service.compute_astronomy_daily(1, lat, lon, test_date)
        
        assert result["location_id"] == 1
        assert result["date"].date() == test_date
        assert result["sunrise_utc"] is not None
        assert result["sunset_utc"] is not None
        assert result["daylight_minutes"] > 0
        assert 0.0 <= result["moon_phase"] <= 1.0
        assert result["civil_twilight_start_utc"] is not None
        assert result["civil_twilight_end_utc"] is not None
        assert result["generated_at"] is not None

    def test_astronomy_moon_phase_bounds(self):
        """Test moon phase is within valid bounds."""
        service = AstronomyComputationService()
        
        # Test multiple dates to ensure moon phase is always 0-1
        for days_offset in range(30):
            test_date = date(2023, 8, 1) + timedelta(days=days_offset)
            result = service.compute_astronomy_daily(1, 40.7128, -74.0060, test_date)
            
            assert 0.0 <= result["moon_phase"] <= 1.0, f"Moon phase out of bounds for {test_date}"

    def test_astronomy_daylight_positive(self):
        """Test daylight minutes is positive for normal latitudes."""
        service = AstronomyComputationService()
        
        # Test for various locations
        locations = [
            (40.7128, -74.0060),  # New York
            (51.5074, -0.1278),   # London
            (35.6762, 139.6503)   # Tokyo
        ]
        
        test_date = date(2023, 6, 21)  # Summer solstice
        
        for lat, lon in locations:
            result = service.compute_astronomy_daily(1, lat, lon, test_date)
            assert result["daylight_minutes"] > 0, f"No daylight for {lat}, {lon}"


@pytest.mark.asyncio
async def test_provider_integration():
    """Integration test for provider system."""
    # This would require actual API calls or more sophisticated mocking
    # For now, just test that providers can be instantiated
    
    forecast_provider = OpenMeteoForecastProvider()
    observation_provider = OpenMeteoObservationProvider()
    air_quality_provider = OpenMeteoAirQualityProvider()
    astronomy_service = AstronomyComputationService()
    
    assert forecast_provider.provider_name == "openmeteo"
    assert observation_provider.provider_name == "openmeteo"
    assert air_quality_provider.provider_name == "openmeteo"
    
    # Test astronomy service doesn't require async
    result = astronomy_service.compute_astronomy_daily(1, 40.7128, -74.0060, date.today())
    assert result is not None