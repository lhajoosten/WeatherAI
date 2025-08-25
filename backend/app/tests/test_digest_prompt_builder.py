"""Tests for the digest prompt builder."""

import json
from unittest.mock import mock_open, patch

import pytest

from ai.builders.digest_prompt_builder import (
    ALLOWED_PREFERENCE_KEYS,
    MAX_TEXT_LENGTHS,
    MORNING_DIGEST_PROMPT_VERSION,
    DigestPromptBuilder,
    create_digest_prompt_builder,
)


class TestDigestPromptBuilder:
    """Test cases for DigestPromptBuilder."""

    @pytest.fixture
    def mock_prompt_template(self):
        """Mock prompt template content."""
        return "System: Test prompt\nContext:\n{context_json}\nTask: Generate response"

    @pytest.fixture
    def prompt_builder(self, mock_prompt_template):
        """Create prompt builder with mocked template."""
        with patch("builtins.open", mock_open(read_data=mock_prompt_template)):
            return DigestPromptBuilder()

    @pytest.fixture
    def sample_preferences(self):
        """Sample user preferences."""
        return {
            "outdoor_activities": True,
            "temperature_tolerance": "normal",
            "rain_tolerance": "low",
            "units_system": "metric",
            "activity_level": "moderate",
            "time_preference": "morning",
            # Non-whitelisted key (should be filtered out)
            "secret_data": "should not appear"
        }

    @pytest.fixture
    def sample_derived_metrics(self):
        """Sample derived metrics with mock objects."""
        from unittest.mock import Mock

        # Mock time window objects
        peak_rain_window = Mock()
        peak_rain_window.start_hour = 14
        peak_rain_window.end_hour = 16
        peak_rain_window.duration_hours = 2

        lowest_wind_window = Mock()
        lowest_wind_window.start_hour = 6
        lowest_wind_window.end_hour = 9

        # Mock activity block
        activity_block = Mock()
        activity_block.activity_type = "outdoor exercise"
        activity_block.conditions = "ideal for running and cycling"
        activity_block.suitability_score = 0.85
        activity_block.time_window = Mock()
        activity_block.time_window.start_hour = 7
        activity_block.time_window.end_hour = 10

        return {
            "temp_min_c": 15.2,
            "temp_max_c": 24.8,
            "comfort_score": 0.72,
            "peak_rain_window": peak_rain_window,
            "lowest_wind_window": lowest_wind_window,
            "activity_blocks": [activity_block]
        }

    def test_prompt_version_constant(self):
        """Test that the prompt version constant is correct."""
        assert MORNING_DIGEST_PROMPT_VERSION == "morning_digest_v1"

    def test_create_digest_prompt_builder(self, mock_prompt_template):
        """Test factory function creates builder correctly."""
        with patch("builtins.open", mock_open(read_data=mock_prompt_template)):
            builder = create_digest_prompt_builder()
            assert isinstance(builder, DigestPromptBuilder)
            assert builder.prompt_template == mock_prompt_template

    def test_build_context_basic(self, prompt_builder, sample_preferences, sample_derived_metrics):
        """Test basic context building."""
        context = prompt_builder.build_context(
            date="2024-01-15",
            location_name="Amsterdam, Netherlands",
            user_preferences=sample_preferences,
            derived_metrics=sample_derived_metrics
        )

        # Check structure
        assert isinstance(context, dict)
        assert "date" in context
        assert "location" in context
        assert "user_preferences" in context
        assert "derived" in context
        assert "constraints" in context

        # Check values
        assert context["date"] == "2024-01-15"
        assert context["location"] == "Amsterdam, Netherlands"

        # Check constraints
        constraints = context["constraints"]
        assert constraints["max_narrative_sentences"] == 3
        assert constraints["required_bullets"] == 3
        assert constraints["bullet_categories"] == ["weather", "activity", "alert"]
        assert constraints["priority_levels"] == [1, 2, 3]

    def test_sanitize_preferences_whitelist(self, prompt_builder, sample_preferences):
        """Test that preferences are filtered by whitelist."""
        sanitized = prompt_builder._sanitize_preferences(sample_preferences)

        # Should include whitelisted keys
        for key in ALLOWED_PREFERENCE_KEYS:
            if key in sample_preferences:
                assert key in sanitized

        # Should exclude non-whitelisted key
        assert "secret_data" not in sanitized

        # Check specific values
        assert sanitized["outdoor_activities"] is True
        assert sanitized["temperature_tolerance"] == "normal"
        assert sanitized["units_system"] == "metric"

    def test_sanitize_text_length_limits(self, prompt_builder):
        """Test text sanitization and length limits."""
        long_text = "A" * 200  # Longer than max length

        # Test with location name limit (100 chars)
        sanitized = prompt_builder._sanitize_text(long_text, "location_name")
        assert len(sanitized) <= MAX_TEXT_LENGTHS["location_name"]

        # Test newline and quote removal
        messy_text = 'Text with\nnewlines\rand "quotes"'
        sanitized = prompt_builder._sanitize_text(messy_text, "location_name")
        assert '\n' not in sanitized
        assert '\r' not in sanitized
        assert '"' not in sanitized
        assert "'" in sanitized  # Quotes should be replaced with apostrophes

    def test_sanitize_derived_metrics(self, prompt_builder, sample_derived_metrics):
        """Test sanitization of derived metrics."""
        sanitized = prompt_builder._sanitize_derived_metrics(sample_derived_metrics)

        # Check numeric fields
        assert sanitized["temp_min_c"] == 15.2
        assert sanitized["temp_max_c"] == 24.8
        assert sanitized["comfort_score"] == 0.72

        # Check time windows
        assert "peak_rain_window" in sanitized
        peak_window = sanitized["peak_rain_window"]
        assert peak_window["start_hour"] == 14
        assert peak_window["end_hour"] == 16
        assert peak_window["duration_hours"] == 2

        # Check activity blocks
        assert "activity_blocks" in sanitized
        assert len(sanitized["activity_blocks"]) == 1

        block = sanitized["activity_blocks"][0]
        assert block["activity_type"] == "outdoor exercise"
        assert block["conditions"] == "ideal for running and cycling"
        assert block["suitability_score"] == 0.85
        assert "time_window" in block
        assert block["time_window"]["start_hour"] == 7

    def test_build_prompt_integration(self, prompt_builder, sample_preferences, sample_derived_metrics):
        """Test complete prompt building integration."""
        prompt = prompt_builder.build_prompt(
            date="2024-01-15",
            location_name="Amsterdam",
            user_preferences=sample_preferences,
            derived_metrics=sample_derived_metrics
        )

        # Check prompt contains template
        assert "System: Test prompt" in prompt
        assert "Task: Generate response" in prompt

        # Check context JSON is embedded
        assert "Amsterdam" in prompt
        assert "2024-01-15" in prompt
        assert "outdoor_activities" in prompt

        # Verify context is valid JSON
        start = prompt.find('{')
        end = prompt.rfind('}') + 1
        context_json = prompt[start:end]
        context = json.loads(context_json)

        assert context["date"] == "2024-01-15"
        assert context["location"] == "Amsterdam"

    def test_build_context_with_style_examples(self, prompt_builder, sample_preferences, sample_derived_metrics):
        """Test context building with style examples."""
        style_examples = {
            "good_narrative": "Clear, concise weather summary",
            "good_bullets": ["Specific action item", "Time-based recommendation"]
        }

        context = prompt_builder.build_context(
            date="2024-01-15",
            location_name="Test Location",
            user_preferences=sample_preferences,
            derived_metrics=sample_derived_metrics,
            style_examples=style_examples
        )

        assert "style_examples" in context
        assert context["style_examples"] == style_examples

    def test_prompt_template_loading_error(self):
        """Test error handling when prompt template file is missing."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError, match="Morning digest prompt template not found"):
                DigestPromptBuilder()

    def test_sanitize_preferences_with_complex_types(self, prompt_builder):
        """Test preference sanitization with various data types."""
        preferences = {
            "outdoor_activities": True,
            "temperature_tolerance": 25.5,  # float
            "rain_tolerance": 3,  # int
            "units_system": ["metric", "imperial"],  # list (should be stringified)
            "activity_level": {"high": True},  # dict (should be stringified)
        }

        sanitized = prompt_builder._sanitize_preferences(preferences)

        assert sanitized["outdoor_activities"] is True
        assert sanitized["temperature_tolerance"] == 25.5
        assert sanitized["rain_tolerance"] == 3
        assert isinstance(sanitized["units_system"], str)
        assert isinstance(sanitized["activity_level"], str)

    def test_sanitize_derived_metrics_missing_fields(self, prompt_builder):
        """Test derived metrics sanitization with missing optional fields."""
        minimal_derived = {
            "temp_min_c": 10.0,
            "temp_max_c": 20.0,
            "comfort_score": 0.5
        }

        sanitized = prompt_builder._sanitize_derived_metrics(minimal_derived)

        assert sanitized["temp_min_c"] == 10.0
        assert sanitized["temp_max_c"] == 20.0
        assert sanitized["comfort_score"] == 0.5
        assert "peak_rain_window" not in sanitized
        assert "activity_blocks" not in sanitized
