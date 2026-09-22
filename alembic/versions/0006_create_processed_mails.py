"""create processed mails

Revision ID: 0006_create_processed_mails
Revises: 0005_create_notification_tables
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_create_processed_mails"
down_revision = "0005_create_notification_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_mails",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=False),
        sa.Column("mailbox", sa.String(length=200), nullable=False),
        sa.Column("remote_id", sa.String(length=200), nullable=False),
        sa.Column("message_id", sa.String(length=500), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "mailbox", "remote_id", name="uq_processed_mails_remote"),
    )


def downgrade() -> None:
    op.drop_table("processed_mails")
