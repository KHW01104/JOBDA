"""create job matches

Revision ID: 0007_create_job_matches
Revises: 0006_create_processed_mails
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_create_job_matches"
down_revision = "0006_create_processed_mails"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_matches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("filter_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["filter_id"], ["user_filters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", "filter_id", name="uq_job_matches_user_job_filter"),
    )
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"])
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"])
    op.create_index("ix_job_matches_filter_id", "job_matches", ["filter_id"])


def downgrade() -> None:
    op.drop_table("job_matches")
