"""In-memory event bus for domain events.

This provides a simple synchronous event bus implementation
for handling domain events within the application.
"""

from __future__ import annotations

from collections.abc import Callable

import structlog

from app.domain.events import BaseDomainEvent

logger = structlog.get_logger(__name__)


class EventBus:
    """Simple in-memory event bus for domain events."""

    def __init__(self):
        self._handlers: dict[str, list[Callable[[BaseDomainEvent], None]]] = {}

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[BaseDomainEvent], None]
    ) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info("Event handler registered", event_type=event_type, handler=handler.__name__)

    def publish(self, event: BaseDomainEvent) -> None:
        """Publish a domain event to all registered handlers."""
        event_type = event.event_type
        handlers = self._handlers.get(event_type, [])

        logger.info(
            "Publishing domain event",
            event_type=event_type,
            event_id=str(event.event_id),
            aggregate_id=event.aggregate_id,
            handler_count=len(handlers)
        )

        for handler in handlers:
            try:
                handler(event)
                logger.debug("Event handler executed successfully", handler=handler.__name__)
            except Exception as e:
                logger.error(
                    "Event handler failed",
                    handler=handler.__name__,
                    error=str(e),
                    event_id=str(event.event_id)
                )
                # Continue processing other handlers even if one fails

    def get_handler_count(self, event_type: str) -> int:
        """Get the number of handlers registered for an event type."""
        return len(self._handlers.get(event_type, []))


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return _event_bus


# Sample event handlers for demonstration
def log_data_ingested(event: BaseDomainEvent) -> None:
    """Sample handler that logs data ingestion events."""
    from app.domain.events import DataIngestedEvent
    if isinstance(event, DataIngestedEvent):
        logger.info(
            "Data ingested",
            location_id=event.aggregate_id,
            provider=event.provider,
            data_type=event.data_type,
            record_count=event.record_count
        )


def log_rag_query_answered(event: BaseDomainEvent) -> None:
    """Sample handler that logs RAG query events."""
    from app.domain.events import RAGQueryAnsweredEvent
    if isinstance(event, RAGQueryAnsweredEvent):
        logger.info(
            "RAG query answered",
            user_id=event.aggregate_id,
            query_length=len(event.query),
            answer_length=event.answer_length,
            sources_count=event.sources_count
        )


# Register sample handlers
def register_default_handlers() -> None:
    """Register default event handlers."""
    bus = get_event_bus()
    bus.register_handler("data.ingested", log_data_ingested)
    bus.register_handler("rag.query.answered", log_rag_query_answered)
