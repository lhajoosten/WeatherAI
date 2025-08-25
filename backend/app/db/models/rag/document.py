"""RAG Document model for the rag schema."""

from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, String, func
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from .base import RagBase


class Document(RagBase):
    """Documents ingested into the RAG system."""
    __tablename__ = "documents"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid4, index=True)
    source_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    # Index for efficient queries
    __table_args__ = (
        Index('ix_documents_source_id', 'source_id'),
    )
