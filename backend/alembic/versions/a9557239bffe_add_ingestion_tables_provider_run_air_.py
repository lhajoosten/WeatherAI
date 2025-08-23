"""Add ingestion tables - provider_run, air_quality_hourly, astronomy_daily

Revision ID: a9557239bffe
Revises: 24d3fcd30cb4
Create Date: 2025-08-23 19:21:05.027651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a9557239bffe'
down_revision: Union[str, Sequence[str], None] = '24d3fcd30cb4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create provider_run table
    op.create_table('provider_run',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=100), nullable=False),
        sa.Column('run_type', sa.String(length=50), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('records_ingested', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_provider_run_id'), 'provider_run', ['id'], unique=False)
    op.create_index('ix_provider_run_provider_type_started', 'provider_run', ['provider', 'run_type', 'started_at'], unique=False)
    
    # Create air_quality_hourly table
    op.create_table('air_quality_hourly',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('observed_at', sa.DateTime(), nullable=False),
        sa.Column('pm10', sa.Float(), nullable=True),
        sa.Column('pm2_5', sa.Float(), nullable=True),
        sa.Column('ozone', sa.Float(), nullable=True),
        sa.Column('no2', sa.Float(), nullable=True),
        sa.Column('so2', sa.Float(), nullable=True),
        sa.Column('pollen_tree', sa.Float(), nullable=True),
        sa.Column('pollen_grass', sa.Float(), nullable=True),
        sa.Column('pollen_weed', sa.Float(), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('raw_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_air_quality_hourly_id'), 'air_quality_hourly', ['id'], unique=False)
    op.create_index('ix_air_quality_hourly_location_time', 'air_quality_hourly', ['location_id', 'observed_at'], unique=False)
    op.create_index('ix_air_quality_hourly_location_time_source', 'air_quality_hourly', ['location_id', 'observed_at', 'source'], unique=True)
    
    # Create astronomy_daily table  
    op.create_table('astronomy_daily',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('sunrise_utc', sa.DateTime(), nullable=True),
        sa.Column('sunset_utc', sa.DateTime(), nullable=True),
        sa.Column('daylight_minutes', sa.Integer(), nullable=True),
        sa.Column('moon_phase', sa.Float(), nullable=True),
        sa.Column('civil_twilight_start_utc', sa.DateTime(), nullable=True),
        sa.Column('civil_twilight_end_utc', sa.DateTime(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_astronomy_daily_id'), 'astronomy_daily', ['id'], unique=False)
    op.create_index('ix_astronomy_daily_location_date', 'astronomy_daily', ['location_id', 'date'], unique=True)
    
    # Add optional columns to llm_audit for forward compatibility
    op.add_column('llm_audit', sa.Column('has_air_quality', sa.Boolean(), nullable=True))
    op.add_column('llm_audit', sa.Column('has_astronomy', sa.Boolean(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop optional llm_audit columns
    op.drop_column('llm_audit', 'has_astronomy')
    op.drop_column('llm_audit', 'has_air_quality')
    
    # Drop astronomy_daily table
    op.drop_index('ix_astronomy_daily_location_date', table_name='astronomy_daily')
    op.drop_index(op.f('ix_astronomy_daily_id'), table_name='astronomy_daily')
    op.drop_table('astronomy_daily')
    
    # Drop air_quality_hourly table
    op.drop_index('ix_air_quality_hourly_location_time_source', table_name='air_quality_hourly')
    op.drop_index('ix_air_quality_hourly_location_time', table_name='air_quality_hourly')
    op.drop_index(op.f('ix_air_quality_hourly_id'), table_name='air_quality_hourly')
    op.drop_table('air_quality_hourly')
    
    # Drop provider_run table
    op.drop_index('ix_provider_run_provider_type_started', table_name='provider_run')
    op.drop_index(op.f('ix_provider_run_id'), table_name='provider_run')
    op.drop_table('provider_run')
