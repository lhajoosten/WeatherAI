"""Unit tests for the domain layer."""

import pytest
from datetime import datetime
from uuid import UUID

from app.domain.exceptions import (
    DomainError, ValidationError, NotFoundError, ConflictError,
    LowSimilarityError
)
from app.domain.events import (
    DataIngestedEvent, RAGQueryAnsweredEvent, DigestGeneratedEvent
)
from app.domain.value_objects import (
    LocationId, UserId, Coordinates, Temperature, DigestType
)


class TestDomainExceptions:
    """Test domain exception hierarchy."""
    
    def test_domain_error_base(self):
        """Test base domain error."""
        error = DomainError("Test error", details="Test details")
        assert str(error) == "Test error"
        assert error.details == "Test details"
        assert error.extra_data == {}
    
    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid input")
        assert isinstance(error, DomainError)
        assert str(error) == "Invalid input"
    
    def test_not_found_error(self):
        """Test not found error."""
        error = NotFoundError("Resource not found")
        assert isinstance(error, DomainError)
        assert str(error) == "Resource not found"
    
    def test_low_similarity_error(self):
        """Test RAG low similarity error."""
        error = LowSimilarityError(threshold=0.7, max_similarity=0.3)
        assert isinstance(error, DomainError)
        assert error.threshold == 0.7
        assert error.max_similarity == 0.3
        assert "0.7" in str(error)
        assert "0.300" in str(error)


class TestDomainEvents:
    """Test domain events."""
    
    def test_data_ingested_event(self):
        """Test data ingested event creation."""
        event = DataIngestedEvent(
            location_id="loc_123",
            provider="test_provider",
            data_type="weather",
            record_count=10
        )
        
        assert event.aggregate_id == "loc_123"
        assert event.provider == "test_provider"
        assert event.data_type == "weather"
        assert event.record_count == 10
        assert event.event_type == "data.ingested"
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
    
    def test_rag_query_answered_event(self):
        """Test RAG query answered event."""
        event = RAGQueryAnsweredEvent(
            user_id="user_123",
            query="What is the weather?",
            answer_length=100,
            sources_count=3
        )
        
        assert event.aggregate_id == "user_123"
        assert event.query == "What is the weather?"
        assert event.answer_length == 100
        assert event.sources_count == 3
        assert event.event_type == "rag.query.answered"
    
    def test_digest_generated_event(self):
        """Test digest generated event."""
        event = DigestGeneratedEvent(
            user_id="user_123",
            location_id="loc_456",
            digest_type="daily"
        )
        
        assert event.aggregate_id == "user_123"
        assert event.location_id == "loc_456"
        assert event.digest_type == "daily"
        assert event.event_type == "digest.generated"


class TestValueObjects:
    """Test domain value objects."""
    
    def test_location_id(self):
        """Test LocationId value object."""
        location_id = LocationId(123)
        assert location_id.value == 123
        
        # Test immutability
        with pytest.raises(AttributeError):
            location_id.value = 456
    
    def test_location_id_validation(self):
        """Test LocationId validation."""
        with pytest.raises(ValueError, match="LocationId must be positive"):
            LocationId(0)
        
        with pytest.raises(ValueError, match="LocationId must be positive"):
            LocationId(-1)
    
    def test_coordinates(self):
        """Test Coordinates value object."""
        coords = Coordinates(latitude=52.3676, longitude=4.9041)
        assert coords.latitude == 52.3676
        assert coords.longitude == 4.9041
    
    def test_coordinates_validation(self):
        """Test Coordinates validation."""
        # Valid coordinates
        Coordinates(0, 0)
        Coordinates(90, 180)
        Coordinates(-90, -180)
        
        # Invalid latitude
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            Coordinates(91, 0)
        
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            Coordinates(-91, 0)
        
        # Invalid longitude
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            Coordinates(0, 181)
        
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            Coordinates(0, -181)
    
    def test_temperature(self):
        """Test Temperature value object."""
        temp = Temperature(20.0, "celsius")
        assert temp.value == 20.0
        assert temp.unit == "celsius"
    
    def test_temperature_validation(self):
        """Test Temperature validation."""
        # Valid temperatures
        Temperature(20.0, "celsius")
        Temperature(68.0, "fahrenheit")
        Temperature(293.15, "kelvin")
        
        # Invalid unit
        with pytest.raises(ValueError, match="Temperature unit must be"):
            Temperature(20.0, "invalid")
        
        # Invalid kelvin (negative)
        with pytest.raises(ValueError, match="Kelvin temperature cannot be negative"):
            Temperature(-10, "kelvin")
    
    def test_temperature_conversion(self):
        """Test temperature conversion."""
        celsius = Temperature(20.0, "celsius")
        
        # Convert to itself
        same = celsius.to_celsius()
        assert same.value == 20.0
        assert same.unit == "celsius"
        
        # Convert from Fahrenheit
        fahrenheit = Temperature(68.0, "fahrenheit")
        converted = fahrenheit.to_celsius()
        assert abs(converted.value - 20.0) < 0.1
        assert converted.unit == "celsius"
        
        # Convert from Kelvin
        kelvin = Temperature(293.15, "kelvin")
        converted = kelvin.to_celsius()
        assert abs(converted.value - 20.0) < 0.1
        assert converted.unit == "celsius"
    
    def test_digest_type(self):
        """Test DigestType value object."""
        digest_type = DigestType("daily")
        assert digest_type.value == "daily"
        
        # Valid types
        DigestType("hourly")
        DigestType("weekly")
        DigestType("custom")
        
        # Invalid type
        with pytest.raises(ValueError, match="DigestType must be one of"):
            DigestType("invalid")