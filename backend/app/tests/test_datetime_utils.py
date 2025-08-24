"""Tests for datetime utility functions."""
import pytest
from datetime import datetime, timezone

from app.core.datetime_utils import parse_iso_utc, truncate_error_message


class TestParseIsoUtc:
    """Test parse_iso_utc function for consistent timezone handling."""
    
    def test_parse_naive_datetime_assumes_utc(self):
        """Test that naive datetime is assumed to be UTC."""
        naive_dt = datetime(2023, 12, 25, 15, 30, 0)
        result = parse_iso_utc(naive_dt)
        
        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 15
        assert result.minute == 30
    
    def test_parse_aware_datetime_converts_to_utc(self):
        """Test that timezone-aware datetime is converted to UTC."""
        # Create datetime with non-UTC timezone
        from datetime import timezone, timedelta
        eastern = timezone(timedelta(hours=-5))  # EST
        aware_dt = datetime(2023, 12, 25, 15, 30, 0, tzinfo=eastern)
        
        result = parse_iso_utc(aware_dt)
        
        assert result.tzinfo == timezone.utc
        # Should be converted to UTC (15:30 EST = 20:30 UTC)
        assert result.hour == 20
        assert result.minute == 30
    
    def test_parse_utc_datetime_unchanged(self):
        """Test that UTC datetime remains unchanged."""
        utc_dt = datetime(2023, 12, 25, 15, 30, 0, tzinfo=timezone.utc)
        result = parse_iso_utc(utc_dt)
        
        assert result == utc_dt
        assert result.tzinfo == timezone.utc
    
    def test_parse_iso_string_with_z_suffix(self):
        """Test parsing ISO string with Z suffix."""
        iso_string = "2023-12-25T15:30:00Z"
        result = parse_iso_utc(iso_string)
        
        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 15
        assert result.minute == 30
    
    def test_parse_iso_string_with_utc_offset(self):
        """Test parsing ISO string with explicit UTC offset."""
        iso_string = "2023-12-25T15:30:00+00:00"
        result = parse_iso_utc(iso_string)
        
        assert result.tzinfo == timezone.utc
        assert result.year == 2023
        assert result.month == 12
        assert result.day == 25
        assert result.hour == 15
        assert result.minute == 30
    
    def test_parse_iso_string_with_timezone_converts(self):
        """Test parsing ISO string with timezone converts to UTC."""
        iso_string = "2023-12-25T15:30:00-05:00"  # EST
        result = parse_iso_utc(iso_string)
        
        assert result.tzinfo == timezone.utc
        # Should be converted to UTC (15:30 EST = 20:30 UTC)
        assert result.hour == 20
        assert result.minute == 30
    
    def test_parse_naive_iso_string_assumes_utc(self):
        """Test that naive ISO string is assumed to be UTC."""
        iso_string = "2023-12-25T15:30:00"
        result = parse_iso_utc(iso_string)
        
        assert result.tzinfo == timezone.utc
        assert result.hour == 15
        assert result.minute == 30
    
    def test_parse_invalid_string_raises_error(self):
        """Test that invalid string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid datetime format"):
            parse_iso_utc("invalid-datetime-string")
    
    def test_parse_unsupported_type_raises_error(self):
        """Test that unsupported type raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported datetime type"):
            parse_iso_utc(12345)


class TestTruncateErrorMessage:
    """Test truncate_error_message function."""
    
    def test_short_message_unchanged(self):
        """Test that short message is unchanged."""
        short_msg = "Short error message"
        result = truncate_error_message(short_msg, max_length=500)
        assert result == short_msg
    
    def test_long_message_truncated(self):
        """Test that long message is truncated with ellipsis."""
        long_msg = "A" * 600  # 600 character message
        result = truncate_error_message(long_msg, max_length=500)
        
        assert len(result) == 500
        assert result.endswith("...")
        assert result == "A" * 497 + "..."
    
    def test_exact_length_unchanged(self):
        """Test that message exactly at max length is unchanged."""
        exact_msg = "A" * 500
        result = truncate_error_message(exact_msg, max_length=500)
        assert result == exact_msg
    
    def test_custom_max_length(self):
        """Test with custom max length."""
        msg = "A" * 100
        result = truncate_error_message(msg, max_length=50)
        
        assert len(result) == 50
        assert result.endswith("...")
        assert result == "A" * 47 + "..."