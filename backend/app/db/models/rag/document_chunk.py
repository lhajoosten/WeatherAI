"""RAG Document Chunk model for the rag schema."""

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship

from .base import RagBase


class DocumentChunk(RagBase):
    """Text chunks from documents for vector retrieval."""
    __tablename__ = "document_chunks"

    id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid4, index=True)
    document_id = Column(UNIQUEIDENTIFIER, ForeignKey("rag.documents.id"), nullable=False, index=True)
    idx = Column(Integer, nullable=False)  # Index within document
    content = Column(Text, nullable=False)
    content_hash = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")

    # Indexes for efficient queries including unique constraint on document_id, idx
    __table_args__ = (
        Index('ix_document_chunks_document_idx', 'document_id', 'idx', unique=True),
        Index('ix_document_chunks_content_hash', 'content_hash'),
    )
