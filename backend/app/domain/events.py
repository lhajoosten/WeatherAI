"""Domain events system for WeatherAI application.

This module provides:
- Base domain event classes
- Event registration and publishing
- Sample domain events for key business processes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4


class BaseDomainEvent(ABC):
    """Base class for all domain events."""

    def __init__(
        self,
        aggregate_id: str,
        event_id: UUID | None = None,
        occurred_at: datetime | None = None,
        metadata: dict[str, Any] | None = None
    ):
        self.event_id = event_id or uuid4()
        self.aggregate_id = aggregate_id
        self.occurred_at = occurred_at or datetime.now(UTC)
        self.metadata = metadata or {}

    @property
    @abstractmethod
    def event_type(self) -> str:
        """The event type identifier."""
        pass


class DataIngestedEvent(BaseDomainEvent):
    """Event raised when weather data is ingested."""

    def __init__(
        self,
        location_id: str,
        provider: str,
        data_type: str,
        record_count: int,
        **kwargs
    ):
        super().__init__(aggregate_id=location_id, **kwargs)
        self.provider = provider
        self.data_type = data_type
        self.record_count = record_count

    @property
    def event_type(self) -> str:
        return "data.ingested"


class RAGQueryAnsweredEvent(BaseDomainEvent):
    """Event raised when a RAG query is successfully answered."""

    def __init__(
        self,
        user_id: str,
        query: str,
        answer_length: int,
        sources_count: int,
        **kwargs
    ):
        super().__init__(aggregate_id=user_id, **kwargs)
        self.query = query
        self.answer_length = answer_length
        self.sources_count = sources_count

    @property
    def event_type(self) -> str:
        return "rag.query.answered"


class DigestGeneratedEvent(BaseDomainEvent):
    """Event raised when a weather digest is generated."""

    def __init__(
        self,
        user_id: str,
        location_id: str,
        digest_type: str,
        **kwargs
    ):
        super().__init__(aggregate_id=user_id, **kwargs)
        self.location_id = location_id
        self.digest_type = digest_type

    @property
    def event_type(self) -> str:
        return "digest.generated"


class UserPreferencesUpdatedEvent(BaseDomainEvent):
    """Event raised when user preferences are updated."""

    def __init__(
        self,
        user_id: str,
        changed_fields: list[str],
        **kwargs
    ):
        super().__init__(aggregate_id=user_id, **kwargs)
        self.changed_fields = changed_fields

    @property
    def event_type(self) -> str:
        return "user.preferences.updated"
