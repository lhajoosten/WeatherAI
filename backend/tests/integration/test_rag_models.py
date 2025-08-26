"""
Tests for the new multi-schema RAG models (Phase 3).

Validates the refactored Document and DocumentChunk models,
including the unique constraint on (document_id, idx).
"""


import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.infrastructure.db.models.rag import Document, DocumentChunk, RagBase


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    # Use SQLite for testing (easier than MSSQL)
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables for the RAG schema
    RagBase.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


class TestRagModels:
    """Test the new RAG domain models."""

    def test_document_model_creation(self, in_memory_db):
        """Test that Document model can be created successfully."""
        session = in_memory_db

        document = Document(
            source_id="test-doc-001"
        )

        session.add(document)
        session.commit()

        # Verify document was created
        assert document.id is not None
        assert document.source_id == "test-doc-001"
        assert document.created_at is not None

    def test_document_source_id_unique_constraint(self, in_memory_db):
        """Test that source_id must be unique across documents."""
        session = in_memory_db

        # Create first document
        doc1 = Document(source_id="duplicate-source")
        session.add(doc1)
        session.commit()

        # Attempt to create second document with same source_id
        doc2 = Document(source_id="duplicate-source")
        session.add(doc2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_document_chunk_creation(self, in_memory_db):
        """Test that DocumentChunk model can be created successfully."""
        session = in_memory_db

        # Create parent document
        document = Document(source_id="test-doc-chunks")
        session.add(document)
        session.commit()

        # Create chunk
        chunk = DocumentChunk(
            document_id=document.id,
            idx=0,
            content="This is a test chunk of content.",
            content_hash="abc123"
        )

        session.add(chunk)
        session.commit()

        # Verify chunk was created
        assert chunk.id is not None
        assert chunk.document_id == document.id
        assert chunk.idx == 0
        assert chunk.content == "This is a test chunk of content."
        assert chunk.content_hash == "abc123"
        assert chunk.created_at is not None

    def test_document_chunk_unique_constraint(self, in_memory_db):
        """Test that (document_id, idx) must be unique for DocumentChunk."""
        session = in_memory_db

        # Create parent document
        document = Document(source_id="test-unique-constraint")
        session.add(document)
        session.commit()

        # Create first chunk with idx=0
        chunk1 = DocumentChunk(
            document_id=document.id,
            idx=0,
            content="First chunk",
            content_hash="hash1"
        )
        session.add(chunk1)
        session.commit()

        # Attempt to create second chunk with same document_id and idx
        chunk2 = DocumentChunk(
            document_id=document.id,
            idx=0,  # Same idx as chunk1
            content="Second chunk (should fail)",
            content_hash="hash2"
        )
        session.add(chunk2)

        # This should raise an IntegrityError due to unique constraint
        with pytest.raises(IntegrityError):
            session.commit()

    def test_document_chunk_different_idx_allowed(self, in_memory_db):
        """Test that chunks with different idx values are allowed for same document."""
        session = in_memory_db

        # Create parent document
        document = Document(source_id="test-different-idx")
        session.add(document)
        session.commit()

        # Create multiple chunks with different idx values
        chunk1 = DocumentChunk(
            document_id=document.id,
            idx=0,
            content="First chunk",
            content_hash="hash1"
        )
        chunk2 = DocumentChunk(
            document_id=document.id,
            idx=1,  # Different idx
            content="Second chunk",
            content_hash="hash2"
        )

        session.add_all([chunk1, chunk2])
        session.commit()

        # Both should be created successfully
        assert chunk1.id is not None
        assert chunk2.id is not None
        assert chunk1.idx == 0
        assert chunk2.idx == 1

    def test_document_chunk_same_idx_different_documents(self, in_memory_db):
        """Test that chunks with same idx are allowed for different documents."""
        session = in_memory_db

        # Create two different documents
        doc1 = Document(source_id="doc-1")
        doc2 = Document(source_id="doc-2")
        session.add_all([doc1, doc2])
        session.commit()

        # Create chunks with same idx but different documents
        chunk1 = DocumentChunk(
            document_id=doc1.id,
            idx=0,
            content="Chunk from doc 1",
            content_hash="hash1"
        )
        chunk2 = DocumentChunk(
            document_id=doc2.id,
            idx=0,  # Same idx but different document
            content="Chunk from doc 2",
            content_hash="hash2"
        )

        session.add_all([chunk1, chunk2])
        session.commit()

        # Both should be created successfully
        assert chunk1.id is not None
        assert chunk2.id is not None
        assert chunk1.document_id == doc1.id
        assert chunk2.document_id == doc2.id

    def test_document_chunk_relationship(self, in_memory_db):
        """Test the relationship between Document and DocumentChunk."""
        session = in_memory_db

        # Create document with chunks
        document = Document(source_id="test-relationship")
        session.add(document)
        session.commit()

        chunks = [
            DocumentChunk(
                document_id=document.id,
                idx=i,
                content=f"Chunk {i}",
                content_hash=f"hash{i}"
            )
            for i in range(3)
        ]

        session.add_all(chunks)
        session.commit()

        # Test forward relationship (document.chunks)
        session.refresh(document)
        assert len(document.chunks) == 3
        assert all(chunk.document_id == document.id for chunk in document.chunks)

        # Test reverse relationship (chunk.document)
        for chunk in chunks:
            session.refresh(chunk)
            assert chunk.document.id == document.id
            assert chunk.document.source_id == "test-relationship"


class TestConstraintMetadata:
    """Test that the constraint metadata is correctly defined."""

    def test_unique_constraint_exists_in_metadata(self):
        """Test that the unique constraint is properly defined in the model metadata."""
        # Check that DocumentChunk has the correct table args
        table_args = DocumentChunk.__table_args__
        assert isinstance(table_args, tuple)

        # Find the unique index
        unique_index = None
        for arg in table_args:
            if hasattr(arg, 'unique') and arg.unique:
                unique_index = arg
                break

        assert unique_index is not None, "DocumentChunk should have a unique constraint"
        assert unique_index.name == 'ix_document_chunks_document_idx'

        # Check column names in the unique constraint
        column_names = [col.name for col in unique_index.expressions]
        assert 'document_id' in column_names
        assert 'idx' in column_names
        assert len(column_names) == 2
