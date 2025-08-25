"""Add digest_audit table for Morning Digest metrics.

Revision ID: 20250825_0002
Revises: 20250825_0001
Create Date: 2025-08-25 14:20:00
"""
from alembic import op
import sqlalchemy as sa

revision = "20250825_0002"
down_revision = "e86d3cc9215f"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "digest_audit",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.Date, nullable=False, index=True),
        sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("cache_hit", sa.Boolean, nullable=False),
        sa.Column("forecast_signature", sa.String(64), nullable=True, index=True),
        sa.Column("preferences_hash", sa.String(64), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True, index=True),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("tokens_in", sa.Integer, nullable=True),
        sa.Column("tokens_out", sa.Integer, nullable=True),
        sa.Column("latency_ms_preprocess", sa.Integer, nullable=True),
        sa.Column("latency_ms_llm", sa.Integer, nullable=True),
        sa.Column("latency_ms_total", sa.Integer, nullable=True),
        sa.Column("reason", sa.String(30), nullable=True),
        sa.Column("comfort_score", sa.Float, nullable=True),
        sa.Column("temp_peak_c", sa.Float, nullable=True),
        sa.Column("temp_peak_hour", sa.Integer, nullable=True),
        sa.Column("wind_peak_kph", sa.Float, nullable=True),
        sa.Column("wind_peak_hour", sa.Integer, nullable=True),
        sa.Column("rain_windows_json", sa.Text, nullable=True),
        sa.Column("activity_block_json", sa.Text, nullable=True),
    )
    op.create_index(
        "ix_digest_audit_user_date",
        "digest_audit",
        ["user_id", "date"],
        unique=False
    )

def downgrade():
    op.drop_index("ix_digest_audit_user_date", table_name="digest_audit")
    op.drop_table("digest_audit")