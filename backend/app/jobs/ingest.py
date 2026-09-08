from datetime import datetime, timezone
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.candidate import JobCandidate
from app.jobs.normalizer import normalize_candidate, normalize_name
from app.models import Company, CompanyType, Job, JobSource, JobSourceType, JobStatus, JobVersion


def ingest_candidate(database: Session, candidate: JobCandidate) -> Job:
    candidate = normalize_candidate(candidate)
    company = database.scalar(select(Company).where(Company.normalized_name == normalize_name(candidate.company)))
    if company is None:
        company = Company(
            name=candidate.company,
            normalized_name=normalize_name(candidate.company),
            company_type=CompanyType.PUBLIC if candidate.source.value == "ALIO" else CompanyType.PRIVATE,
        )
        database.add(company)
        database.flush()

    source_type = JobSourceType(candidate.source.value)
    source = database.scalar(
        select(JobSource).where(
            JobSource.source_type == source_type,
            JobSource.source_job_id == candidate.source_job_id,
        )
    )
    now = datetime.now(timezone.utc)
    if source is None:
        job = Job(
            company=company,
            title=candidate.title,
            normalized_title=normalize_name(candidate.title),
            job_category=candidate.job_category,
            experience_min=candidate.experience_min,
            experience_max=candidate.experience_max,
            experience_type=candidate.experience_type,
            employment_type=candidate.employment_type,
            location=candidate.location,
            education=candidate.education,
            published_at=candidate.published_at,
            deadline=candidate.deadline,
            status=JobStatus(candidate.status),
            canonical_url=candidate.source_url,
        )
        database.add(job)
        database.flush()
        database.add(
            JobSource(
                job=job,
                source_type=source_type,
                source_name=source_type.value,
                source_job_id=candidate.source_job_id,
                source_url=candidate.source_url,
                raw_metadata=candidate.raw_metadata,
            )
        )
        database.add(
            JobVersion(
                job=job,
                version=1,
                title=candidate.title,
                experience=candidate.experience_type,
                employment_type=candidate.employment_type,
                location=candidate.location,
                deadline=candidate.deadline,
                status=JobStatus(candidate.status),
                content_hash=sha256(
                    f"{candidate.title}|{candidate.deadline}|{candidate.status}".encode()
                ).hexdigest(),
            )
        )
        return job

    job = database.get(Job, source.job_id)
    if job is None:
        raise ValueError(f"JobSource {source.id}가 참조하는 Job을 찾을 수 없습니다.")
    job.last_seen_at = now
    job.updated_at = now
    job.title = candidate.title
    job.normalized_title = normalize_name(candidate.title)
    job.deadline = candidate.deadline
    job.status = JobStatus(candidate.status)
    job.canonical_url = candidate.source_url or job.canonical_url
    source.last_seen_at = now
    source.source_url = candidate.source_url or source.source_url
    source.raw_metadata = candidate.raw_metadata
    return job


def ingest_candidates(database: Session, candidates: list[JobCandidate]) -> int:
    for candidate in candidates:
        ingest_candidate(database, candidate)
    database.commit()
    return len(candidates)
