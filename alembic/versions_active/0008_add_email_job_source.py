"""add email job source

Revision ID: 0008_add_email_job_source
Revises: 0007_create_job_matches
Create Date: 2026-09-23
"""

from alembic import op


revision = "0008_add_email_job_source"
down_revision = "0007_create_job_matches"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TYPE jobsourcetype ADD VALUE IF NOT EXISTS 'EMAIL'")


def downgrade() -> None:
    raise RuntimeError("EMAIL 출처 데이터가 존재할 수 있어 jobsourcetype 축소 자동 롤백을 지원하지 않습니다.")
