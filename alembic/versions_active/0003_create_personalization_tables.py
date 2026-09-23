"""create personalization tables

Revision ID: 0003_create_personalization_tables
Revises: 0002_create_job_tables
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_create_personalization_tables"
down_revision = "0002_create_job_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_filters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("job_categories", sa.JSON(), nullable=False),
        sa.Column("experience_min", sa.Integer(), nullable=True),
        sa.Column("experience_max", sa.Integer(), nullable=True),
        sa.Column("locations", sa.JSON(), nullable=False),
        sa.Column("employment_types", sa.JSON(), nullable=False),
        sa.Column("company_sizes", sa.JSON(), nullable=False),
        sa.Column("minimum_employee_count", sa.Integer(), nullable=True),
        sa.Column("included_keywords", sa.JSON(), nullable=False),
        sa.Column("excluded_keywords", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_user_filters_user_id", "user_filters", ["user_id"])

    op.create_table(
        "company_watches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=True),
        sa.Column("company_name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_company_watches_user_id", "company_watches", ["user_id"])
    op.create_index("ix_company_watches_company_id", "company_watches", ["company_id"])

    op.create_table(
        "job_scraps",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SCRAPPED"),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_scraps_user_id", "job_scraps", ["user_id"])
    op.create_index("ix_job_scraps_job_id", "job_scraps", ["job_id"])


def downgrade() -> None:
    op.drop_table("job_scraps")
    op.drop_table("company_watches")
    op.drop_table("user_filters")
