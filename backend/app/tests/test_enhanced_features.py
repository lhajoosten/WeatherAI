from unittest.mock import AsyncMock, Mock

import pytest

from app.services.explain_service import EXPLAIN_PROMPT_VERSION, ExplainService


class MockLocation:
    def __init__(self, id: int, lat: float, lon: float, timezone: str = "UTC"):
        self.id = id
        self.lat = lat
        self.lon = lon
        self.timezone = timezone


@pytest.mark.asyncio
async def test_explain_service_location_variation():
    """Test that different locations produce different mock forecast data."""
    # Setup
    mock_llm_client = AsyncMock()
    mock_forecast_repo = Mock()
    service = ExplainService(mock_llm_client, mock_forecast_repo)

    # Test locations in different hemispheres and latitude bands
    locations = [
        MockLocation(1, 40.7128, -74.0060),  # New York (northern temperate)
        MockLocation(2, -33.8688, 151.2093),  # Sydney (southern temperate)
        MockLocation(3, 1.3521, 103.8198),   # Singapore (tropical)
        MockLocation(4, 64.1466, -21.9426),  # Reykjavik (northern temperate/polar border)
    ]

    # Test derived metadata calculation for each location
    metadata_results = []
    for location in locations:
        metadata = service._get_derived_location_metadata(location)
        metadata_results.append(metadata)

    # Verify different hemispheres
    assert metadata_results[0]["hemisphere"] == "northern"  # New York
    assert metadata_results[1]["hemisphere"] == "southern"  # Sydney
    assert metadata_results[2]["hemisphere"] == "northern"  # Singapore
    assert metadata_results[3]["hemisphere"] == "northern"  # Reykjavik

    # Verify different latitude bands
    assert metadata_results[0]["lat_band"] == "temperate"  # New York
    assert metadata_results[1]["lat_band"] == "temperate"  # Sydney
    assert metadata_results[2]["lat_band"] == "tropical"   # Singapore
    assert metadata_results[3]["lat_band"] == "polar"      # Reykjavik (64° is polar)

    # Test variation seed generation
    seeds = []
    for location in locations:
        seed = service._get_location_variation_seed(location.id, location.lat, location.lon)
        seeds.append(seed)

    # Verify seeds are different for different locations
    assert len(set(seeds)) == len(seeds), "All location seeds should be unique"

    # Verify seeds are deterministic (same inputs = same output)
    seed1 = service._get_location_variation_seed(1, 40.7128, -74.0060)
    seed2 = service._get_location_variation_seed(1, 40.7128, -74.0060)
    assert seed1 == seed2, "Variation seed should be deterministic"

    # Verify seeds are in expected range
    for seed in seeds:
        assert -1.0 <= seed <= 1.0, f"Seed {seed} should be between -1 and 1"


@pytest.mark.asyncio
async def test_explain_service_prompt_version():
    """Test that explain service uses the correct prompt version."""
    # Setup
    mock_llm_client = AsyncMock()
    mock_llm_client.generate.return_value = {
        "text": "Summary: Test weather\n\nActions:\n- Action 1\n- Action 2\n- Action 3\n\nDriver: Test driver",
        "tokens_in": 100,
        "tokens_out": 50,
        "model": "gpt-4"
    }

    mock_forecast_repo = AsyncMock()
    mock_forecast_repo.get_latest_for_location.return_value = None
    mock_forecast_repo.create = AsyncMock()

    # Create mock session for location lookup
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = MockLocation(1, 40.7, -74.0)
    mock_session.execute.return_value = mock_result
    mock_forecast_repo.session = mock_session

    service = ExplainService(mock_llm_client, mock_forecast_repo)
    location = MockLocation(1, 40.7128, -74.0060, "America/New_York")

    # Call explain method
    await service.explain_location_weather(location, user_id=123)

    # Verify LLM client was called with correct parameters
    mock_llm_client.generate.assert_called_once()
    call_args = mock_llm_client.generate.call_args

    assert call_args[1]["prompt_version"] == EXPLAIN_PROMPT_VERSION
    assert call_args[1]["location_id"] == location.id
    assert call_args[1]["user_id"] == 123
    assert call_args[1]["endpoint"] == "explain"
    assert call_args[1]["temperature"] == 0.1


def test_explain_prompt_version_constant():
    """Test that the prompt version constant is set correctly."""
    assert EXPLAIN_PROMPT_VERSION == "explain_v2"


def test_derived_metadata_calculations():
    """Test specific derived metadata calculations."""
    service = ExplainService(None, None)

    # Test tropical latitude
    tropical_location = MockLocation(1, 15.0, 100.0)
    metadata = service._get_derived_location_metadata(tropical_location)
    assert metadata["lat_band"] == "tropical"
    assert metadata["hemisphere"] == "northern"

    # Test southern hemisphere tropical
    south_tropical = MockLocation(2, -10.0, 150.0)
    metadata = service._get_derived_location_metadata(south_tropical)
    assert metadata["lat_band"] == "tropical"
    assert metadata["hemisphere"] == "southern"

    # Test polar region
    polar_location = MockLocation(3, 70.0, -150.0)
    metadata = service._get_derived_location_metadata(polar_location)
    assert metadata["lat_band"] == "polar"
    assert metadata["hemisphere"] == "northern"

    # Test temperate boundaries
    temperate_edge = MockLocation(4, 50.0, 0.0)
    metadata = service._get_derived_location_metadata(temperate_edge)
    assert metadata["lat_band"] == "temperate"

    # Test timezone handling
    ny_location = MockLocation(5, 40.7, -74.0, "America/New_York")
    metadata = service._get_derived_location_metadata(ny_location)
    assert "local_datetime_now" in metadata
    assert "daylight_flag" in metadata
    assert isinstance(metadata["daylight_flag"], bool)


@pytest.mark.asyncio
async def test_location_crud_operations():
    """Test location update and delete operations."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.repositories import LocationRepository

    # Mock session and location
    mock_session = AsyncMock(spec=AsyncSession)
    repo = LocationRepository(mock_session)

    # Mock location object
    mock_location = Mock()
    mock_location.name = "Original Name"
    mock_location.timezone = "UTC"

    # Test update operation
    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_location

    result = await repo.update(1, 123, name="Updated Name", timezone="America/New_York")

    assert result == mock_location
    assert mock_location.name == "Updated Name"
    assert mock_location.timezone == "America/New_York"
    mock_session.commit.assert_called_once()
    mock_session.refresh.assert_called_once_with(mock_location)


@pytest.mark.asyncio
async def test_geocoding_cache():
    """Test geocoding service caching functionality."""
    from unittest.mock import patch

    from app.api.v1.routes.geo import GeocodingService

    service = GeocodingService()

    # Mock httpx response
    mock_response_data = {
        "results": [
            {
                "name": "New York",
                "country": "United States",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "timezone": "America/New_York",
                "admin1": "New York",
                "admin2": ""
            }
        ]
    }

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status.return_value = None

        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        # First call should hit the API
        result1 = await service.search("New York")
        assert len(result1) == 1
        assert result1[0]["name"] == "New York"
        assert result1[0]["display_name"] == "New York, New York, United States"

        # Clear the client mock to verify cache hit
        mock_client.reset_mock()

        # Second call should use cache (no API call)
        result2 = await service.search("new york")  # Different case
        assert result1 == result2
        mock_client.assert_not_called()  # Should not make another API call
