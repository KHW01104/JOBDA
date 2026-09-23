"""repair missing job version field changes

Revision ID: 0009_repair_field_changes
Revises: 0008_add_email_job_source
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_repair_field_changes"
down_revision = "0008_add_email_job_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("job_versions")}
    if "field_changes" not in columns:
        op.add_column("job_versions", sa.Column("field_changes", sa.JSON(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in sa.inspect(bind).get_columns("job_versions")}
    if "field_changes" in columns:
        op.drop_column("job_versions", "field_changes")
