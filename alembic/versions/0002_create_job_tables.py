"""create job tables

Revision ID: 0002_create_job_tables
Revises: 0001_create_users
Create Date: 2026-09-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_create_job_tables"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    company_type = sa.Enum("PRIVATE", "PUBLIC", "UNKNOWN", name="companytype")
    job_status = sa.Enum("OPEN", "CLOSED", "UNKNOWN", name="jobstatus")
    source_type = sa.Enum("SARAMIN", "ALIO", name="jobsourcetype")
    bind = op.get_bind()
    company_type.create(bind, checkfirst=True)
    job_status.create(bind, checkfirst=True)
    source_type.create(bind, checkfirst=True)

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("normalized_name", sa.String(length=200), nullable=False),
        sa.Column("company_type", company_type, nullable=False),
        sa.Column("company_size", sa.String(length=30), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_index("ix_companies_normalized_name", "companies", ["normalized_name"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("normalized_title", sa.String(length=300), nullable=False),
        sa.Column("job_category", sa.String(length=100), nullable=True),
        sa.Column("experience_min", sa.Integer(), nullable=True),
        sa.Column("experience_max", sa.Integer(), nullable=True),
        sa.Column("experience_type", sa.String(length=30), nullable=True),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("education", sa.String(length=100), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", job_status, nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"])
    op.create_index("ix_jobs_normalized_title", "jobs", ["normalized_title"])

    op.create_table(
        "job_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("source_job_id", sa.String(length=200), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("raw_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_sources_job_id", "job_sources", ["job_id"])

    op.create_table(
        "job_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("experience", sa.String(length=100), nullable=True),
        sa.Column("employment_type", sa.String(length=50), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("requirements", sa.Text(), nullable=True),
        sa.Column("preferences", sa.Text(), nullable=True),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("status", job_status, nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_versions_job_id", "job_versions", ["job_id"])


def downgrade() -> None:
    op.drop_table("job_versions")
    op.drop_table("job_sources")
    op.drop_table("jobs")
    op.drop_table("companies")
    bind = op.get_bind()
    sa.Enum(name="jobsourcetype").drop(bind, checkfirst=True)
    sa.Enum(name="jobstatus").drop(bind, checkfirst=True)
    sa.Enum(name="companytype").drop(bind, checkfirst=True)
