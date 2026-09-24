"""create recruitment schedules

Revision ID: 0010_recruitment_schedules
Revises: 0009_repair_field_changes
Create Date: 2026-09-24
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_recruitment_schedules"
down_revision = "0009_repair_field_changes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recruitment_schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("mail_remote_id", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mail_remote_id"),
    )


def downgrade() -> None:
    op.drop_table("recruitment_schedules")
