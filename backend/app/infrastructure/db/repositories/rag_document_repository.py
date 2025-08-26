"""RAG document repository (rag schema)."""

from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.infrastructure.db.models.rag import Document, DocumentChunk


class RagDocumentRepository:
    """Repository for RAG document operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, source_id: str) -> Document:
        document = Document(source_id=source_id)
        self.session.add(document)
        await self.session.flush()
        await self.session.refresh(document)
        return document

    async def get_by_source_id(self, source_id: str) -> Document | None:
        result = await self.session.execute(select(Document).where(Document.source_id == source_id))
        return result.scalar_one_or_none()

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self.session.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def bulk_insert_chunks(self, document_id: UUID, chunks_data: List[Dict[str, Any]]) -> List[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for cd in chunks_data:
            chunk = DocumentChunk(
                document_id=document_id,
                idx=cd["idx"],
                content=cd["content"],
                content_hash=cd["content_hash"],
            )
            chunks.append(chunk)
            self.session.add(chunk)
        await self.session.flush()
        for c in chunks:
            await self.session.refresh(c)
        return chunks

    async def get_chunks_by_document_id(self, document_id: UUID) -> List[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.idx)
        )
        return list(result.scalars().all())

    async def delete_document(self, document_id: UUID) -> bool:
        doc = await self.get_by_id(document_id)
        if not doc:
            return False
        await self.session.delete(doc)
        await self.session.flush()
        return True

__all__ = ["RagDocumentRepository"]
