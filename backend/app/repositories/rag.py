"""RAG document repository for handling document and chunk persistence."""

from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.models.rag import Document, DocumentChunk
from .base import BaseRepository


class RagDocumentRepository(BaseRepository):
    """Repository for RAG document operations."""

    async def create_document(self, source_id: str) -> Document:
        """Create a new RAG document."""
        document = Document(source_id=source_id)
        self.session.add(document)
        await self.session.flush()  # Don't commit yet - let UoW handle it
        await self.session.refresh(document)
        return document

    async def get_by_source_id(self, source_id: str) -> Document | None:
        """Get document by source ID."""
        result = await self.session.execute(
            select(Document).where(Document.source_id == source_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, document_id: UUID) -> Document | None:
        """Get document by ID."""
        result = await self.session.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def bulk_insert_chunks(
        self, 
        document_id: UUID, 
        chunks_data: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Bulk insert chunks for a document.
        
        Args:
            document_id: UUID of the parent document
            chunks_data: List of dicts with keys: idx, content, content_hash
            
        Returns:
            List of created DocumentChunk objects
        """
        chunks = []
        for chunk_data in chunks_data:
            chunk = DocumentChunk(
                document_id=document_id,
                idx=chunk_data["idx"],
                content=chunk_data["content"],
                content_hash=chunk_data["content_hash"],
            )
            chunks.append(chunk)
            self.session.add(chunk)
        
        await self.session.flush()  # Don't commit yet - let UoW handle it
        
        # Refresh all chunks to get their IDs
        for chunk in chunks:
            await self.session.refresh(chunk)
        
        return chunks

    async def get_chunks_by_document_id(self, document_id: UUID) -> List[DocumentChunk]:
        """Get all chunks for a document, ordered by index."""
        result = await self.session.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.idx)
        )
        return list(result.scalars().all())

    async def delete_document(self, document_id: UUID) -> bool:
        """Delete a document and all its chunks."""
        document = await self.get_by_id(document_id)
        if not document:
            return False
        
        await self.session.delete(document)
        await self.session.flush()  # Don't commit yet - let UoW handle it
        return True