"""Tests for the Azure digest client."""

import json
from unittest.mock import AsyncMock

import pytest

from app.ai.llm.azure_client import (
    AzureDigestClient,
    DigestSummary,
    LLMResult,
    create_azure_digest_client,
)


class TestAzureDigestClient:
    """Test cases for AzureDigestClient."""

    @pytest.fixture
    def mock_llm_client(self):
        """Mock LLM client."""
        return AsyncMock()

    @pytest.fixture
    def azure_client(self, mock_llm_client):
        """Create AzureDigestClient with mocked dependencies."""
        return AzureDigestClient(mock_llm_client)

    @pytest.fixture
    def valid_llm_response(self):
        """Valid LLM response content."""
        return {
            "narrative": "Today's weather will be pleasant with temperatures ranging from 15°C to 24°C. Light winds and clear skies make it ideal for outdoor activities.",
            "bullets": [
                {
                    "text": "Comfortable temperature range 15°C-24°C - ideal for most outdoor activities",
                    "category": "weather",
                    "priority": 2
                },
                {
                    "text": "Best time for outdoor exercise: 7 AM-10 AM (ideal conditions)",
                    "category": "activity",
                    "priority": 1
                },
                {
                    "text": "Excellent overall conditions - perfect day for any planned outdoor activities",
                    "category": "weather",
                    "priority": 2
                }
            ],
            "driver": "favorable weather conditions"
        }

    @pytest.fixture
    def sample_context(self):
        """Sample context for digest generation."""
        return {
            "date": "2024-01-15",
            "location": "Amsterdam",
            "user_preferences": {
                "outdoor_activities": True,
                "temperature_tolerance": "normal"
            },
            "derived": {
                "temp_min_c": 15.2,
                "temp_max_c": 24.8,
                "comfort_score": 0.72
            },
            "constraints": {
                "max_narrative_sentences": 3,
                "required_bullets": 3
            }
        }

    def test_create_azure_digest_client(self, mock_llm_client):
        """Test factory function."""
        client = create_azure_digest_client(mock_llm_client)
        assert isinstance(client, AzureDigestClient)
        assert client.llm_client == mock_llm_client

    def test_initialization(self, mock_llm_client):
        """Test client initialization."""
        client = AzureDigestClient(mock_llm_client)

        assert client.llm_client == mock_llm_client
        assert client.temperature == 0.1
        assert client.max_tokens == 500
        assert client.max_retries == 3

    @pytest.mark.asyncio
    async def test_generate_digest_summary_success(self, azure_client, mock_llm_client, valid_llm_response, sample_context):
        """Test successful digest generation."""
        # Setup mock LLM response
        mock_llm_client.generate.return_value = {
            "text": json.dumps(valid_llm_response),
            "tokens_in": 150,
            "tokens_out": 85,
            "model": "gpt-4"
        }

        # Generate digest
        result = await azure_client.generate_digest_summary(
            context=sample_context,
            prompt="Test prompt with context",
            user_id=123,
            location_id=456
        )

        # Verify result
        assert isinstance(result, LLMResult)
        assert result.content == json.dumps(valid_llm_response)
        assert result.tokens_in == 150
        assert result.tokens_out == 85
        assert result.model == "gpt-4"
        assert result.duration_ms > 0
        assert result.cost_usd is not None
        assert result.cost_usd > 0

        # Verify LLM client was called correctly
        mock_llm_client.generate.assert_called_once_with(
            prompt="Test prompt with context",
            user_id=123,
            endpoint="morning_digest",
            temperature=0.1,
            max_tokens=500,
            prompt_version="morning_digest_v1",
            location_id=456
        )

    def test_parse_and_validate_response_valid(self, azure_client, valid_llm_response):
        """Test parsing valid response."""
        content = json.dumps(valid_llm_response)
        summary = azure_client._parse_and_validate_response(content)

        assert isinstance(summary, DigestSummary)
        assert summary.narrative == valid_llm_response["narrative"]
        assert summary.bullets == valid_llm_response["bullets"]
        assert summary.driver == valid_llm_response["driver"]

    def test_parse_and_validate_response_wrapped_json(self, azure_client, valid_llm_response):
        """Test parsing JSON wrapped in extra text."""
        json_content = json.dumps(valid_llm_response)
        wrapped_content = f"Here is the response:\n{json_content}\nThank you."

        summary = azure_client._parse_and_validate_response(wrapped_content)
        assert isinstance(summary, DigestSummary)
        assert summary.narrative == valid_llm_response["narrative"]

    def test_parse_and_validate_response_invalid_json(self, azure_client):
        """Test error handling for invalid JSON."""
        invalid_content = "This is not JSON at all"

        with pytest.raises(json.JSONDecodeError):
            azure_client._parse_and_validate_response(invalid_content)

    def test_parse_and_validate_response_missing_fields(self, azure_client):
        """Test validation with missing required fields."""
        invalid_response = {
            "narrative": "Test narrative",
            # Missing bullets and driver
        }

        with pytest.raises(ValueError, match="Missing required field"):
            azure_client._parse_and_validate_response(json.dumps(invalid_response))

    def test_parse_and_validate_response_wrong_bullet_count(self, azure_client):
        """Test validation with wrong number of bullets."""
        invalid_response = {
            "narrative": "Test narrative",
            "bullets": [
                {"text": "Only one bullet", "category": "weather", "priority": 1}
            ],
            "driver": "test driver"
        }

        with pytest.raises(ValueError, match="Expected exactly 3 bullets"):
            azure_client._parse_and_validate_response(json.dumps(invalid_response))

    def test_parse_and_validate_response_invalid_bullet_category(self, azure_client):
        """Test validation with invalid bullet category."""
        invalid_response = {
            "narrative": "Test narrative",
            "bullets": [
                {"text": "Bullet 1", "category": "invalid_category", "priority": 1},
                {"text": "Bullet 2", "category": "weather", "priority": 1},
                {"text": "Bullet 3", "category": "activity", "priority": 1}
            ],
            "driver": "test driver"
        }

        with pytest.raises(ValueError, match="invalid category"):
            azure_client._parse_and_validate_response(json.dumps(invalid_response))

    def test_parse_and_validate_response_invalid_bullet_priority(self, azure_client):
        """Test validation with invalid bullet priority."""
        invalid_response = {
            "narrative": "Test narrative",
            "bullets": [
                {"text": "Bullet 1", "category": "weather", "priority": 5},  # Invalid priority
                {"text": "Bullet 2", "category": "weather", "priority": 1},
                {"text": "Bullet 3", "category": "activity", "priority": 1}
            ],
            "driver": "test driver"
        }

        with pytest.raises(ValueError, match="invalid priority"):
            azure_client._parse_and_validate_response(json.dumps(invalid_response))

    def test_estimate_cost_gpt4(self, azure_client):
        """Test cost estimation for GPT-4."""
        cost = azure_client._estimate_cost(1000, 500, "gpt-4")

        # GPT-4: $0.03/1k input, $0.06/1k output
        expected = (1000/1000 * 0.03) + (500/1000 * 0.06)
        assert cost == pytest.approx(expected, rel=1e-6)

    def test_estimate_cost_unknown_model(self, azure_client):
        """Test cost estimation falls back to GPT-4 pricing for unknown models."""
        cost_unknown = azure_client._estimate_cost(1000, 500, "unknown-model")
        cost_gpt4 = azure_client._estimate_cost(1000, 500, "gpt-4")

        assert cost_unknown == cost_gpt4

    @pytest.mark.asyncio
    async def test_generate_digest_summary_with_retries(self, azure_client, mock_llm_client, valid_llm_response):
        """Test retry logic on failures."""
        # First two calls fail, third succeeds
        mock_llm_client.generate.side_effect = [
            Exception("Network error"),
            Exception("Timeout error"),
            {
                "text": json.dumps(valid_llm_response),
                "tokens_in": 150,
                "tokens_out": 85,
                "model": "gpt-4"
            }
        ]

        # Should succeed after retries
        result = await azure_client.generate_digest_summary(
            context={},
            prompt="test prompt"
        )

        assert isinstance(result, LLMResult)
        assert mock_llm_client.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_digest_summary_max_retries_exceeded(self, azure_client, mock_llm_client):
        """Test failure after maximum retries."""
        # All calls fail
        mock_llm_client.generate.side_effect = Exception("Persistent error")

        # Import the exception
        from app.core.exceptions import DigestGenerationError

        with pytest.raises(DigestGenerationError, match="Failed to generate digest after 3 attempts"):
            await azure_client.generate_digest_summary(
                context={},
                prompt="test prompt"
            )

        assert mock_llm_client.generate.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_digest_summary_json_validation_retries(self, azure_client, mock_llm_client, valid_llm_response):
        """Test retry on JSON validation failures."""
        # First call returns invalid JSON, second succeeds
        mock_llm_client.generate.side_effect = [
            {"text": "Invalid JSON response", "tokens_in": 100, "tokens_out": 50, "model": "gpt-4"},
            {"text": json.dumps(valid_llm_response), "tokens_in": 150, "tokens_out": 85, "model": "gpt-4"}
        ]

        result = await azure_client.generate_digest_summary(
            context={},
            prompt="test prompt"
        )

        assert isinstance(result, LLMResult)
        assert mock_llm_client.generate.call_count == 2
