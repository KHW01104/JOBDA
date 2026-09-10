"""add job version field changes

Revision ID: 0004_add_job_version_field_changes
Revises: 0003_create_personalization_tables
Create Date: 2026-09-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_add_job_version_field_changes"
down_revision = "0003_create_personalization_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_versions", sa.Column("field_changes", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_versions", "field_changes")
