"""merge_heads

Revision ID: ec60fa052f34
Revises: 8a9f5e3d2b1c, add_location_groups
Create Date: 2025-08-24 07:58:29.956010

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec60fa052f34'
down_revision: Union[str, Sequence[str], None] = ('8a9f5e3d2b1c', 'add_location_groups')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
