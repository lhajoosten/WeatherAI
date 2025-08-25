"""Add RAG documents and chunks tables

Revision ID: 20250825_0003_add_rag_tables
Revises: 20250825_0002_add_digest_audit
Create Date: 2025-08-25 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = '20250825_0003_add_rag_tables'
down_revision = '20250825_0002_add_digest_audit'
branch_labels = None
depends_on = None


def upgrade():
    # Create rag_documents table
    op.create_table('rag_documents',
        sa.Column('id', mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column('source_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('getdate()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_id')
    )
    op.create_index('ix_rag_documents_id', 'rag_documents', ['id'], unique=False)
    op.create_index('ix_rag_documents_source_id', 'rag_documents', ['source_id'], unique=False)

    # Create rag_document_chunks table
    op.create_table('rag_document_chunks',
        sa.Column('id', mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column('document_id', mssql.UNIQUEIDENTIFIER(), nullable=False),
        sa.Column('idx', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('getdate()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['rag_documents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_rag_chunks_content_hash', 'rag_document_chunks', ['content_hash'], unique=False)
    op.create_index('ix_rag_chunks_document_idx', 'rag_document_chunks', ['document_id', 'idx'], unique=False)
    op.create_index('ix_rag_document_chunks_document_id', 'rag_document_chunks', ['document_id'], unique=False)
    op.create_index('ix_rag_document_chunks_id', 'rag_document_chunks', ['id'], unique=False)


def downgrade():
    # Drop rag_document_chunks table
    op.drop_index('ix_rag_document_chunks_id', table_name='rag_document_chunks')
    op.drop_index('ix_rag_document_chunks_document_id', table_name='rag_document_chunks')
    op.drop_index('ix_rag_chunks_document_idx', table_name='rag_document_chunks')
    op.drop_index('ix_rag_chunks_content_hash', table_name='rag_document_chunks')
    op.drop_table('rag_document_chunks')

    # Drop rag_documents table
    op.drop_index('ix_rag_documents_source_id', table_name='rag_documents')
    op.drop_index('ix_rag_documents_id', table_name='rag_documents')
    op.drop_table('rag_documents')