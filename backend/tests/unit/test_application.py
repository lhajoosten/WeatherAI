"""Unit tests for the application layer."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.event_bus import EventBus, register_default_handlers
from app.domain.events import DataIngestedEvent, RAGQueryAnsweredEvent


class TestEventBus:
    """Test the event bus implementation."""
    
    def test_event_bus_creation(self):
        """Test event bus creation."""
        bus = EventBus()
        assert bus.get_handler_count("test.event") == 0
    
    def test_register_handler(self):
        """Test handler registration."""
        bus = EventBus()
        
        def test_handler(event):
            pass
        
        bus.register_handler("test.event", test_handler)
        assert bus.get_handler_count("test.event") == 1
    
    def test_multiple_handlers(self):
        """Test multiple handlers for same event."""
        bus = EventBus()
        
        def handler1(event):
            pass
        
        def handler2(event):
            pass
        
        bus.register_handler("test.event", handler1)
        bus.register_handler("test.event", handler2)
        
        assert bus.get_handler_count("test.event") == 2
    
    def test_publish_event(self):
        """Test event publishing."""
        bus = EventBus()
        handler_called = False
        received_event = None
        
        def test_handler(event):
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event
        
        bus.register_handler("data.ingested", test_handler)
        
        event = DataIngestedEvent(
            location_id="test_loc",
            provider="test_provider",
            data_type="weather",
            record_count=5
        )
        
        bus.publish(event)
        
        assert handler_called
        assert received_event == event
    
    def test_publish_no_handlers(self):
        """Test publishing event with no handlers."""
        bus = EventBus()
        
        event = DataIngestedEvent(
            location_id="test_loc",
            provider="test_provider",
            data_type="weather",
            record_count=5
        )
        
        # Should not raise exception
        bus.publish(event)
    
    def test_handler_exception_handling(self):
        """Test that handler exceptions don't stop other handlers."""
        bus = EventBus()
        handler1_called = False
        handler2_called = False
        
        def failing_handler(event):
            nonlocal handler1_called
            handler1_called = True
            raise Exception("Handler failed")
        
        def working_handler(event):
            nonlocal handler2_called
            handler2_called = True
        
        bus.register_handler("data.ingested", failing_handler)
        bus.register_handler("data.ingested", working_handler)
        
        event = DataIngestedEvent(
            location_id="test_loc",
            provider="test_provider",
            data_type="weather",
            record_count=5
        )
        
        bus.publish(event)
        
        # Both handlers should have been called
        assert handler1_called
        assert handler2_called
    
    def test_default_handlers_registration(self):
        """Test default handlers registration."""
        bus = EventBus()
        
        # Mock the handlers
        original_handlers = {}
        
        def mock_log_data_ingested(event):
            pass
        
        def mock_log_rag_query(event):
            pass
        
        # Register handlers
        bus.register_handler("data.ingested", mock_log_data_ingested)
        bus.register_handler("rag.query.answered", mock_log_rag_query)
        
        assert bus.get_handler_count("data.ingested") == 1
        assert bus.get_handler_count("rag.query.answered") == 1