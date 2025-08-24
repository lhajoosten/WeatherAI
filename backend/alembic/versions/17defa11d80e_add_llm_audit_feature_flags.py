"""add_llm_audit_feature_flags

Revision ID: 17defa11d80e
Revises: ec60fa052f34
Create Date: 2025-08-24 07:58:36.438369

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17defa11d80e'
down_revision: Union[str, Sequence[str], None] = 'ec60fa052f34'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add feature flag columns to llm_audit table
    op.add_column('llm_audit', sa.Column('has_air_quality', sa.Boolean(), nullable=True, default=False))
    op.add_column('llm_audit', sa.Column('has_astronomy', sa.Boolean(), nullable=True, default=False))
    
    # Backfill existing rows with False values
    op.execute("UPDATE llm_audit SET has_air_quality = 0, has_astronomy = 0 WHERE has_air_quality IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the feature flag columns
    op.drop_column('llm_audit', 'has_astronomy')
    op.drop_column('llm_audit', 'has_air_quality')
