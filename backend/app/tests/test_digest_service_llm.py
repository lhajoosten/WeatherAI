"""Tests for the LLM-integrated digest service."""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.schemas.digest import DigestResponse, TokensMeta
from app.services.digest_service import DigestService


class TestDigestServiceLLM:
    """Test cases for DigestService with LLM integration."""

    @pytest.fixture
    def mock_forecast_provider(self):
        """Mock forecast provider."""
        provider = AsyncMock()
        provider.get_forecast.return_value = {
            "hourly": [
                {"temperature": 20, "hour": 0, "precipitation": 0, "wind_speed": 10},
                {"temperature": 25, "hour": 12, "precipitation": 1.2, "wind_speed": 8},
                {"temperature": 18, "hour": 23, "precipitation": 0, "wind_speed": 12}
            ]
        }
        return provider

    @pytest.fixture
    def mock_preferences_provider(self):
        """Mock preferences provider."""
        provider = AsyncMock()
        provider.get_preferences.return_value = {
            "outdoor_activities": True,
            "temperature_tolerance": "normal",
            "rain_tolerance": "low",
            "units_system": "metric"
        }
        return provider

    @pytest.fixture
    def mock_llm_audit_repo(self):
        """Mock LLM audit repository."""
        return AsyncMock()

    @pytest.fixture
    def valid_llm_response(self):
        """Valid LLM response."""
        return {
            "narrative": "Today's weather will be pleasant with temperatures ranging from 18°C to 25°C. Light winds and minimal rainfall make it ideal for outdoor activities.",
            "bullets": [
                {
                    "text": "Comfortable temperature range 18°C-25°C - ideal for most outdoor activities",
                    "category": "weather",
                    "priority": 2
                },
                {
                    "text": "Best time for outdoor activities: 12 PM with warmest conditions",
                    "category": "activity",
                    "priority": 1
                },
                {
                    "text": "Light rain possible - bring light jacket for temperature changes",
                    "category": "alert",
                    "priority": 2
                }
            ],
            "driver": "favorable weather conditions"
        }

    def test_initialization_with_llm(self, mock_forecast_provider, mock_preferences_provider, mock_llm_audit_repo):
        """Test service initialization with LLM enabled."""
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            llm_audit_repo=mock_llm_audit_repo,
            use_llm=True
        )

        assert service.use_llm is True
        assert service.llm_client is not None
        assert service.azure_client is not None
        assert service.prompt_builder is not None

    def test_initialization_without_llm(self, mock_forecast_provider, mock_preferences_provider):
        """Test service initialization with LLM disabled."""
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            use_llm=False
        )

        assert service.use_llm is False
        assert service.llm_client is None
        assert service.azure_client is None
        assert service.prompt_builder is None

    @pytest.mark.asyncio
    async def test_generate_digest_with_llm_success(
        self,
        mock_forecast_provider,
        mock_preferences_provider,
        mock_llm_audit_repo,
        valid_llm_response
    ):
        """Test successful digest generation with LLM."""
        # Create service
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            llm_audit_repo=mock_llm_audit_repo,
            use_llm=True
        )

        # Mock the LLM client generate method
        service.llm_client.generate = AsyncMock(return_value={
            "text": json.dumps(valid_llm_response),
            "tokens_in": 200,
            "tokens_out": 120,
            "model": "gpt-4"
        })

        # Mock cache to force generation
        with patch('app.services.digest_service.digest_cache') as mock_cache:
            mock_cache.get_digest.return_value = None  # Cache miss
            mock_cache.set_digest = AsyncMock()
            mock_cache._generate_cache_key.return_value = "test_cache_key"

            # Generate digest
            result = await service.get_morning_digest(
                user_id="123",
                date="2024-01-15",
                force=True
            )

        # Verify result
        assert isinstance(result, DigestResponse)
        assert result.summary.narrative == valid_llm_response["narrative"]
        assert len(result.summary.bullets) == 3
        assert result.summary.driver == valid_llm_response["driver"]

        # Verify tokens meta is populated
        assert result.tokens_meta is not None
        assert result.tokens_meta.tokens_in == 200
        assert result.tokens_meta.tokens_out == 120
        assert result.tokens_meta.model == "gpt-4"
        assert result.tokens_meta.cost_usd is not None

        # Verify cache metadata
        assert result.cache_meta.hit is False

    @pytest.mark.asyncio
    async def test_generate_digest_llm_fallback_to_placeholder(
        self,
        mock_forecast_provider,
        mock_preferences_provider,
        mock_llm_audit_repo
    ):
        """Test fallback to placeholder when LLM fails."""
        # Create service
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            llm_audit_repo=mock_llm_audit_repo,
            use_llm=True
        )

        # Mock the LLM client to fail
        service.llm_client.generate = AsyncMock(side_effect=Exception("LLM service unavailable"))

        # Mock cache to force generation
        with patch('app.services.digest_service.digest_cache') as mock_cache:
            mock_cache.get_digest.return_value = None  # Cache miss
            mock_cache.set_digest = AsyncMock()
            mock_cache._generate_cache_key.return_value = "test_cache_key"

            # Generate digest
            result = await service.get_morning_digest(
                user_id="123",
                date="2024-01-15",
                force=True
            )

        # Verify result falls back gracefully
        assert isinstance(result, DigestResponse)
        assert result.summary.narrative is not None  # Placeholder narrative
        assert len(result.summary.bullets) == 3     # Placeholder bullets

        # Verify tokens meta shows fallback
        assert result.tokens_meta is not None
        assert result.tokens_meta.model == "placeholder-fallback"
        assert result.tokens_meta.cost_usd == 0.0

    @pytest.mark.asyncio
    async def test_generate_digest_without_llm_uses_placeholder(
        self,
        mock_forecast_provider,
        mock_preferences_provider
    ):
        """Test that disabling LLM uses placeholder generation."""
        # Create service without LLM
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            use_llm=False
        )

        # Mock cache to force generation
        with patch('app.services.digest_service.digest_cache') as mock_cache:
            mock_cache.get_digest.return_value = None  # Cache miss
            mock_cache.set_digest = AsyncMock()
            mock_cache._generate_cache_key.return_value = "test_cache_key"

            # Generate digest
            result = await service.get_morning_digest(
                user_id="123",
                date="2024-01-15",
                force=True
            )

        # Verify result uses placeholder
        assert isinstance(result, DigestResponse)
        assert result.summary.narrative is not None
        assert len(result.summary.bullets) == 3

        # Verify no tokens meta (placeholder mode)
        assert result.tokens_meta is None

    @pytest.mark.asyncio
    async def test_llm_summary_generation_method(
        self,
        mock_forecast_provider,
        mock_preferences_provider,
        mock_llm_audit_repo,
        valid_llm_response
    ):
        """Test the internal _generate_llm_summary method."""
        # Create service
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            llm_audit_repo=mock_llm_audit_repo,
            use_llm=True
        )

        # Mock the Azure client
        service.azure_client.generate_digest_summary = AsyncMock(return_value=Mock(
            content=json.dumps(valid_llm_response),
            tokens_in=150,
            tokens_out=90,
            model="gpt-4",
            cost_usd=0.0072,
            duration_ms=1200
        ))

        # Mock derived data
        derived_data = {
            "temp_min_c": 18.0,
            "temp_max_c": 25.0,
            "comfort_score": 0.8,
            "peak_rain_window": None,
            "activity_blocks": []
        }

        user_preferences = {
            "outdoor_activities": True,
            "temperature_tolerance": "normal"
        }

        # Call the method
        summary, tokens_meta = await service._generate_llm_summary(
            derived_data=derived_data,
            user_preferences=user_preferences,
            date="2024-01-15",
            location_id=1,
            user_id="123"
        )

        # Verify summary
        assert summary.narrative == valid_llm_response["narrative"]
        assert len(summary.bullets) == 3
        assert summary.driver == valid_llm_response["driver"]

        # Verify tokens meta
        assert isinstance(tokens_meta, TokensMeta)
        assert tokens_meta.tokens_in == 150
        assert tokens_meta.tokens_out == 90
        assert tokens_meta.model == "gpt-4"
        assert tokens_meta.cost_usd == 0.0072

    @pytest.mark.asyncio
    async def test_llm_summary_generation_invalid_json_fallback(
        self,
        mock_forecast_provider,
        mock_preferences_provider,
        mock_llm_audit_repo
    ):
        """Test fallback when LLM returns invalid JSON."""
        # Create service
        service = DigestService(
            forecast_provider=mock_forecast_provider,
            preferences_provider=mock_preferences_provider,
            llm_audit_repo=mock_llm_audit_repo,
            use_llm=True
        )

        # Mock the Azure client to return invalid JSON
        service.azure_client.generate_digest_summary = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))

        # Mock derived data
        derived_data = {
            "temp_min_c": 18.0,
            "temp_max_c": 25.0,
            "comfort_score": 0.8,
            "peak_rain_window": None,
            "activity_blocks": []
        }

        user_preferences = {"outdoor_activities": True}

        # Call the method - should fallback gracefully
        summary, tokens_meta = await service._generate_llm_summary(
            derived_data=derived_data,
            user_preferences=user_preferences,
            date="2024-01-15",
            location_id=1,
            user_id="123"
        )

        # Verify fallback to placeholder
        assert summary.narrative is not None  # Placeholder narrative
        assert len(summary.bullets) == 3     # Placeholder bullets
        assert tokens_meta.model == "placeholder-fallback"
        assert tokens_meta.cost_usd == 0.0
