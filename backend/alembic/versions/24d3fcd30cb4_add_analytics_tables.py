"""Add analytics tables

Revision ID: 24d3fcd30cb4
Revises: 742fe8dc4791
Create Date: 2025-08-23 15:07:20.189616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24d3fcd30cb4'
down_revision: Union[str, Sequence[str], None] = '742fe8dc4791'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create observation_hourly table
    op.create_table('observation_hourly',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('observed_at', sa.DateTime(), nullable=False),
        sa.Column('temp_c', sa.Float(), nullable=True),
        sa.Column('wind_kph', sa.Float(), nullable=True),
        sa.Column('precip_mm', sa.Float(), nullable=True),
        sa.Column('humidity_pct', sa.Float(), nullable=True),
        sa.Column('condition_code', sa.String(length=100), nullable=True),
        sa.Column('source', sa.String(length=100), nullable=False),
        sa.Column('raw_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_observation_hourly_id'), 'observation_hourly', ['id'], unique=False)
    op.create_index('ix_observation_hourly_location_time', 'observation_hourly', ['location_id', 'observed_at'], unique=False)
    
    # Create forecast_hourly table
    op.create_table('forecast_hourly',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('forecast_issue_time', sa.DateTime(), nullable=False),
        sa.Column('target_time', sa.DateTime(), nullable=False),
        sa.Column('temp_c', sa.Float(), nullable=True),
        sa.Column('precipitation_probability_pct', sa.Float(), nullable=True),
        sa.Column('wind_kph', sa.Float(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('source_run_id', sa.String(length=100), nullable=True),
        sa.Column('raw_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forecast_hourly_id'), 'forecast_hourly', ['id'], unique=False)
    op.create_index('ix_forecast_hourly_location_target', 'forecast_hourly', ['location_id', 'target_time'], unique=False)
    
    # Create aggregation_daily table
    op.create_table('aggregation_daily',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('temp_min_c', sa.Float(), nullable=True),
        sa.Column('temp_max_c', sa.Float(), nullable=True),
        sa.Column('avg_temp_c', sa.Float(), nullable=True),
        sa.Column('total_precip_mm', sa.Float(), nullable=True),
        sa.Column('max_wind_kph', sa.Float(), nullable=True),
        sa.Column('heating_degree_days', sa.Float(), nullable=True),
        sa.Column('cooling_degree_days', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aggregation_daily_id'), 'aggregation_daily', ['id'], unique=False)
    op.create_index('ix_aggregation_daily_location_date', 'aggregation_daily', ['location_id', 'date'], unique=False)
    
    # Create forecast_accuracy table
    op.create_table('forecast_accuracy',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('target_time', sa.DateTime(), nullable=False),
        sa.Column('forecast_issue_time', sa.DateTime(), nullable=False),
        sa.Column('variable', sa.String(length=50), nullable=False),
        sa.Column('forecast_value', sa.Float(), nullable=True),
        sa.Column('observed_value', sa.Float(), nullable=True),
        sa.Column('abs_error', sa.Float(), nullable=True),
        sa.Column('pct_error', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forecast_accuracy_id'), 'forecast_accuracy', ['id'], unique=False)
    op.create_index('ix_forecast_accuracy_location_target', 'forecast_accuracy', ['location_id', 'target_time'], unique=False)
    
    # Create trend_cache table
    op.create_table('trend_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('location_id', sa.Integer(), nullable=False),
        sa.Column('metric', sa.String(length=100), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('previous_value', sa.Float(), nullable=True),
        sa.Column('delta', sa.Float(), nullable=True),
        sa.Column('pct_change', sa.Float(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trend_cache_id'), 'trend_cache', ['id'], unique=False)
    op.create_index('ix_trend_cache_unique', 'trend_cache', ['location_id', 'metric', 'period'], unique=True)
    
    # Create analytics_query_audit table
    op.create_table('analytics_query_audit',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('endpoint', sa.String(length=100), nullable=False),
        sa.Column('params_json', sa.Text(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('rows_returned', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analytics_query_audit_id'), 'analytics_query_audit', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_analytics_query_audit_id'), table_name='analytics_query_audit')
    op.drop_table('analytics_query_audit')
    op.drop_index('ix_trend_cache_unique', table_name='trend_cache')
    op.drop_index(op.f('ix_trend_cache_id'), table_name='trend_cache')
    op.drop_table('trend_cache')
    op.drop_index('ix_forecast_accuracy_location_target', table_name='forecast_accuracy')
    op.drop_index(op.f('ix_forecast_accuracy_id'), table_name='forecast_accuracy')
    op.drop_table('forecast_accuracy')
    op.drop_index('ix_aggregation_daily_location_date', table_name='aggregation_daily')
    op.drop_index(op.f('ix_aggregation_daily_id'), table_name='aggregation_daily')
    op.drop_table('aggregation_daily')
    op.drop_index('ix_forecast_hourly_location_target', table_name='forecast_hourly')
    op.drop_index(op.f('ix_forecast_hourly_id'), table_name='forecast_hourly')
    op.drop_table('forecast_hourly')
    op.drop_index('ix_observation_hourly_location_time', table_name='observation_hourly')
    op.drop_index(op.f('ix_observation_hourly_id'), table_name='observation_hourly')
    op.drop_table('observation_hourly')
