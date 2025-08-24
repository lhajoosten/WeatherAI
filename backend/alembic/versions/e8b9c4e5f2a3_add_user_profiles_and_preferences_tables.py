"""add_user_profiles_and_preferences_tables

Revision ID: e8b9c4e5f2a3
Revises: add_location_groups_add_location_groups
Create Date: 2025-01-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey, Index


# revision identifiers, used by Alembic.
revision = 'e8b9c4e5f2a3'
down_revision = 'add_location_groups_add_location_groups'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_profiles table
    op.create_table(
        'user_profiles',
        Column('id', Integer, primary_key=True, index=True),
        Column('user_id', Integer, ForeignKey('users.id'), nullable=False, unique=True),
        Column('display_name', String(255), nullable=True),
        Column('bio', String(500), nullable=True),
        Column('avatar_url', String(500), nullable=True),
        Column('time_zone', String(50), nullable=True),
        Column('locale', String(10), nullable=True),
        Column('theme_preference', String(20), nullable=True),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False),
    )
    op.create_index('ix_user_profiles_user_id', 'user_profiles', ['user_id'])

    # Create user_preferences table
    op.create_table(
        'user_preferences',
        Column('id', Integer, primary_key=True, index=True),
        Column('user_id', Integer, ForeignKey('users.id'), nullable=False, unique=True),
        Column('units_system', String(20), nullable=False, default='metric'),
        Column('dashboard_default_location_id', Integer, ForeignKey('locations.id'), nullable=True),
        Column('show_wind', Boolean, nullable=False, default=True),
        Column('show_precip', Boolean, nullable=False, default=True),
        Column('show_humidity', Boolean, nullable=False, default=True),
        Column('json_settings', Text, nullable=True),
        Column('created_at', DateTime, nullable=False),
        Column('updated_at', DateTime, nullable=False),
    )
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
    op.drop_index('ix_user_profiles_user_id', table_name='user_profiles')
    op.drop_table('user_profiles')