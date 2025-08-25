"""Move RAG tables to rag schema and rename

Revision ID: 20250826_0004_move_rag_to_schema
Revises: 20250825_0003_add_rag_tables
Create Date: 2025-08-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250826_0004_move_rag_to_schema'
down_revision = '20250825_0003_add_rag_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Move and rename RAG tables to rag schema."""
    
    # Create schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    op.execute("CREATE SCHEMA IF NOT EXISTS rag")
    
    # Move and rename rag_documents to rag.documents
    op.execute("ALTER TABLE public.rag_documents SET SCHEMA rag")
    op.execute("ALTER TABLE rag.rag_documents RENAME TO documents")
    
    # Move and rename rag_document_chunks to rag.document_chunks  
    op.execute("ALTER TABLE public.rag_document_chunks SET SCHEMA rag")
    op.execute("ALTER TABLE rag.rag_document_chunks RENAME TO document_chunks")
    
    # Update foreign key constraint to reference new table name
    # Drop old constraint and recreate with proper reference
    op.execute("ALTER TABLE rag.document_chunks DROP CONSTRAINT IF EXISTS FK__rag_docum__docum__5FB337D6")
    op.execute("ALTER TABLE rag.document_chunks ADD CONSTRAINT fk_document_chunks_document_id_documents FOREIGN KEY (document_id) REFERENCES rag.documents(id)")
    
    # Rename indexes to follow new naming convention (optional - check actual names in your DB)
    # Note: SQL Server auto-generates index names, so these might differ
    # Check actual index names with: SELECT name FROM sys.indexes WHERE object_id = OBJECT_ID('rag.documents')
    
    # For documents table
    try:
        op.execute("EXEC sp_rename 'rag.documents.ix_rag_documents_id', 'ix_documents_id', 'INDEX'")
    except:
        pass  # Index might not exist or have different name
        
    try:
        op.execute("EXEC sp_rename 'rag.documents.ix_rag_documents_source_id', 'ix_documents_source_id', 'INDEX'")
    except:
        pass
        
    # For document_chunks table  
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_rag_document_chunks_id', 'ix_document_chunks_id', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_rag_document_chunks_document_id', 'ix_document_chunks_document_id', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_rag_chunks_content_hash', 'ix_document_chunks_content_hash', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_rag_chunks_document_idx', 'ix_document_chunks_document_idx', 'INDEX'")
    except:
        pass


def downgrade():
    """Reverse the schema move operation."""
    
    # Rename indexes back (reverse of upgrade, with error handling)
    try:
        op.execute("EXEC sp_rename 'rag.documents.ix_documents_id', 'ix_rag_documents_id', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.documents.ix_documents_source_id', 'ix_rag_documents_source_id', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_document_chunks_id', 'ix_rag_document_chunks_id', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_document_chunks_document_id', 'ix_rag_document_chunks_document_id', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_document_chunks_content_hash', 'ix_rag_chunks_content_hash', 'INDEX'")
    except:
        pass
        
    try:
        op.execute("EXEC sp_rename 'rag.document_chunks.ix_document_chunks_document_idx', 'ix_rag_chunks_document_idx', 'INDEX'")
    except:
        pass
    
    # Drop and recreate foreign key with old name
    op.execute("ALTER TABLE rag.document_chunks DROP CONSTRAINT IF EXISTS fk_document_chunks_document_id_documents")
    
    # Rename tables back to original names
    op.execute("ALTER TABLE rag.documents RENAME TO rag_documents")
    op.execute("ALTER TABLE rag.document_chunks RENAME TO rag_document_chunks")
    
    # Move tables back to public schema
    op.execute("ALTER TABLE rag.rag_documents SET SCHEMA public")
    op.execute("ALTER TABLE rag.rag_document_chunks SET SCHEMA public")
    
    # Recreate original foreign key (let SQL Server auto-name it)
    op.execute("ALTER TABLE public.rag_document_chunks ADD CONSTRAINT FK_rag_document_chunks_document_id FOREIGN KEY (document_id) REFERENCES public.rag_documents(id)")