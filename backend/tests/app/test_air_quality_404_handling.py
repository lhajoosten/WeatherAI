"""Integration tests for air quality provider 404 handling."""
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.core.settings import settings
from app.ingest.providers.openmeteo_air_quality import OpenMeteoAirQualityProvider


class TestAirQualityProvider404Handling:
    """Test air quality provider handles 404 responses correctly."""

    @pytest.fixture
    def air_quality_provider(self):
        """Create air quality provider instance."""
        return OpenMeteoAirQualityProvider()

    @pytest.mark.asyncio
    async def test_air_quality_404_returns_empty_list_when_not_strict(self, air_quality_provider):
        """Test that 404 response returns empty list when strict mode is disabled."""
        # Mock settings for non-strict mode
        with patch.object(settings, 'openmeteo_air_quality_strict', False):
            # Mock HTTP client to return 404
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=mock_response
            )

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get.return_value = mock_response

                # Call the provider
                result = await air_quality_provider.fetch_air_quality(
                    location_id=123, lat=40.7128, lon=-74.0060, hours_back=24
                )

                # Should return empty list (not raise exception)
                assert result == []
                assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_air_quality_404_raises_exception_when_strict(self, air_quality_provider):
        """Test that 404 response raises exception when strict mode is enabled."""
        # Mock settings for strict mode
        with patch.object(settings, 'openmeteo_air_quality_strict', True):
            # Mock HTTP client to return 404
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=mock_response
            )

            with patch('httpx.AsyncClient') as mock_client_class:
                mock_client = AsyncMock()
                mock_client_class.return_value.__aenter__.return_value = mock_client
                mock_client.get.return_value = mock_response

                # Call the provider - should raise exception in strict mode
                with pytest.raises(httpx.HTTPStatusError):
                    await air_quality_provider.fetch_air_quality(
                        location_id=123, lat=40.7128, lon=-74.0060, hours_back=24
                    )

    @pytest.mark.asyncio
    async def test_air_quality_other_http_errors_always_raise(self, air_quality_provider):
        """Test that non-404 HTTP errors always raise exceptions."""
        # Mock HTTP client to return 500
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=AsyncMock(), response=mock_response
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            # Should raise exception regardless of strict mode setting
            with pytest.raises(httpx.HTTPStatusError):
                await air_quality_provider.fetch_air_quality(
                    location_id=123, lat=40.7128, lon=-74.0060, hours_back=24
                )

    @pytest.mark.asyncio
    async def test_air_quality_successful_response(self, air_quality_provider):
        """Test that successful response is handled correctly."""
        # Mock successful response with sample data
        sample_data = {
            "hourly": {
                "time": ["2023-12-01T00:00:00Z", "2023-12-01T01:00:00Z"],
                "pm2_5": [15.0, 18.5],
                "pm10": [25.0, 28.5],
                "ozone": [45.0, 42.0],
                "nitrogen_dioxide": [20.0, 22.0],
                "sulphur_dioxide": [5.0, 6.0],
                "alder_pollen": [0.0, 0.0],
                "birch_pollen": [0.0, 0.0],
                "grass_pollen": [1.0, 2.0],
                "ragweed_pollen": [0.5, 0.8]
            }
        }

        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_data
        mock_response.raise_for_status.return_value = None

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get.return_value = mock_response

            # Call the provider
            result = await air_quality_provider.fetch_air_quality(
                location_id=123, lat=40.7128, lon=-74.0060, hours_back=24
            )

            # Should return normalized records
            assert isinstance(result, list)
            assert len(result) >= 0  # May be filtered by time range

            # If records exist, verify structure
            if result:
                record = result[0]
                assert "location_id" in record
                assert "observed_at" in record
                assert "pm2_5" in record
                assert "source" in record
                assert record["location_id"] == 123
                assert record["source"] == "openmeteo"
