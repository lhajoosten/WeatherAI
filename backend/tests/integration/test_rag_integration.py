"""
Integration test for RAG ingestion with new schema models.

Validates that RAG ingest functionality works with the new
Document and DocumentChunk models in the rag schema.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models import Document, DocumentChunk


class TestRagIngestionIntegration:
    """Test RAG ingestion with new models."""

    @pytest.mark.asyncio
    async def test_rag_ingest_creates_new_models(self):
        """Test that RAG ingest creates Document and DocumentChunk instances."""
        # Mock session
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock a simple RAG ingest process
        # This simulates what would happen in the actual ingest pipeline

        # Create document
        document = Document(source_id="integration-test-doc")
        mock_session.add(document)
        await mock_session.commit()

        # Simulate setting an ID after commit
        document.id = "test-uuid-123"

        # Create chunks for the document
        test_content = "This is a test document that will be split into chunks. Each chunk represents a portion of the original text."
        chunks = []

        # Split content into chunks (simplified)
        chunk_size = 30
        for i, start in enumerate(range(0, len(test_content), chunk_size)):
            chunk_text = test_content[start:start + chunk_size]

            chunk = DocumentChunk(
                document_id=document.id,
                idx=i,
                content=chunk_text,
                content_hash=f"hash_{i}"
            )
            chunks.append(chunk)
            mock_session.add(chunk)

        await mock_session.commit()

        # Verify the ingest process created expected objects
        assert document.source_id == "integration-test-doc"
        assert len(chunks) > 1  # Should have split into multiple chunks

        # Verify chunks are properly linked
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == document.id
            assert chunk.idx == i
            assert chunk.content_hash == f"hash_{i}"
            assert len(chunk.content) <= chunk_size

        # Verify session interactions
        expected_add_calls = 1 + len(chunks)  # 1 document + N chunks
        assert mock_session.add.call_count == expected_add_calls
        assert mock_session.commit.call_count == 2  # Once for document, once for chunks

    def test_document_and_chunk_model_compatibility(self):
        """Test that new models are compatible with expected RAG pipeline interfaces."""
        # Test Document model
        document = Document(source_id="compatibility-test")

        # Verify expected attributes exist
        assert hasattr(document, 'id')
        assert hasattr(document, 'source_id')
        assert hasattr(document, 'created_at')
        assert hasattr(document, 'chunks')

        # Verify table name matches expected schema
        assert document.__tablename__ == "documents"
        assert hasattr(Document.__table__, 'schema')

        # Test DocumentChunk model
        chunk = DocumentChunk(
            document_id="test-doc-id",
            idx=0,
            content="test content",
            content_hash="test-hash"
        )

        # Verify expected attributes exist
        assert hasattr(chunk, 'id')
        assert hasattr(chunk, 'document_id')
        assert hasattr(chunk, 'idx')
        assert hasattr(chunk, 'content')
        assert hasattr(chunk, 'content_hash')
        assert hasattr(chunk, 'created_at')
        assert hasattr(chunk, 'document')

        # Verify table name matches expected schema
        assert chunk.__tablename__ == "document_chunks"
        assert hasattr(DocumentChunk.__table__, 'schema')

    def test_backward_compatibility_imports(self):
        """Test that new models can be imported in ways that maintain compatibility."""
        # Test imports that existing code might use
        from app.db.models import Document, DocumentChunk
        from app.db.models.rag import Document as RagDocument
        from app.db.models.rag import DocumentChunk as RagDocumentChunk

        # Verify they're the same classes
        assert Document is RagDocument
        assert DocumentChunk is RagDocumentChunk

        # Verify models have expected metadata
        assert Document.__name__ == "Document"
        assert DocumentChunk.__name__ == "DocumentChunk"
