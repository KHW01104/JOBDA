from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.candidate import JobCandidate
from app.jobs.change_detector import changed_fields, content_hash, experience_value
from app.jobs.normalizer import company_defaults, normalize_candidate, normalize_name
from app.models import Company, CompanyType, Job, JobMatch, JobSource, JobSourceType, JobStatus, JobVersion, UserFilter
from app.notifications.service import record_scrap_change_events


def find_duplicate_job(database: Session, company: Company, candidate: JobCandidate) -> Job | None:
    if candidate.location is None or candidate.employment_type is None or candidate.deadline is None:
        return None
    return database.scalar(
        select(Job).where(
            Job.company_id == company.id,
            Job.normalized_title == normalize_name(candidate.title),
            Job.location == candidate.location,
            Job.employment_type == candidate.employment_type,
            Job.deadline == candidate.deadline,
        )
    )


def create_job_version(
    job: Job,
    candidate: JobCandidate,
    version: int,
    field_changes: dict[str, dict[str, str | None]] | None = None,
) -> JobVersion:
    return JobVersion(
        job=job,
        version=version,
        title=candidate.title,
        experience=experience_value(candidate),
        employment_type=candidate.employment_type,
        location=candidate.location,
        deadline=candidate.deadline,
        status=JobStatus(candidate.status),
        content_hash=content_hash(candidate),
        field_changes=field_changes,
    )


def update_job(job: Job, candidate: JobCandidate, now: datetime) -> None:
    job.last_seen_at = now
    job.updated_at = now
    job.title = candidate.title
    job.normalized_title = normalize_name(candidate.title)
    job.job_category = candidate.job_category
    job.experience_min = candidate.experience_min
    job.experience_max = candidate.experience_max
    job.experience_type = candidate.experience_type
    job.employment_type = candidate.employment_type
    job.location = candidate.location
    job.education = candidate.education
    job.published_at = candidate.published_at
    job.deadline = candidate.deadline
    job.status = JobStatus(candidate.status)
    job.canonical_url = candidate.source_url or job.canonical_url


def ingest_candidate(database: Session, candidate: JobCandidate) -> Job:
    candidate = normalize_candidate(candidate)
    company = database.scalar(select(Company).where(Company.normalized_name == normalize_name(candidate.company)))
    if company is None:
        company = Company(**company_defaults(candidate))
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
    if candidate.company_size:
        company.company_size = candidate.company_size
    if candidate.employee_count is not None:
        company.employee_count = candidate.employee_count
    if source is None:
        job = find_duplicate_job(database, company, candidate)
        if job is None:
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
            database.add(create_job_version(job, candidate, version=1))
        database.add(
            JobSource(
                job=job,
                source_type=source_type,
                source_name=(candidate.raw_metadata or {}).get("source_platform") or source_type.value,
                source_job_id=candidate.source_job_id,
                source_url=candidate.source_url,
                raw_metadata=candidate.raw_metadata,
            )
        )
        return job

    job = database.get(Job, source.job_id)
    if job is None:
        raise ValueError(f"JobSource {source.id}가 참조하는 Job을 찾을 수 없습니다.")
    field_changes: dict[str, dict[str, str | None]] | None = None
    latest_version = database.scalar(
        select(JobVersion).where(JobVersion.job_id == job.id).order_by(JobVersion.version.desc())
    )
    if latest_version is None:
        database.add(create_job_version(job, candidate, version=1))
    elif latest_version.content_hash != content_hash(candidate):
        field_changes = changed_fields(latest_version, candidate)
        if field_changes:
            database.add(create_job_version(job, candidate, version=latest_version.version + 1, field_changes=field_changes))
    update_job(job, candidate, now)
    source.last_seen_at = now
    source.source_url = candidate.source_url or source.source_url
    source.raw_metadata = candidate.raw_metadata
    if field_changes:
        record_scrap_change_events(database, job, field_changes)
    return job


def ingest_candidates(database: Session, candidates: list[JobCandidate]) -> int:
    for candidate in candidates:
        ingest_candidate(database, candidate)
    database.commit()
    return len(candidates)


def filter_matches_candidate(user_filter: UserFilter, candidate: JobCandidate) -> bool:
    searchable = " ".join(value for value in (candidate.company, candidate.title, candidate.job_category) if value).casefold()
    included_keywords = [keyword.casefold() for keyword in user_filter.included_keywords if keyword.strip()]
    excluded_keywords = [keyword.casefold() for keyword in user_filter.excluded_keywords if keyword.strip()]
    if included_keywords and not any(keyword in searchable for keyword in included_keywords):
        return False
    if any(keyword in searchable for keyword in excluded_keywords):
        return False
    if user_filter.job_categories and candidate.job_category not in user_filter.job_categories:
        return False
    if user_filter.locations and candidate.location not in user_filter.locations:
        return False
    if user_filter.employment_types and candidate.employment_type not in user_filter.employment_types:
        return False
    if user_filter.experience_min is not None and (candidate.experience_min is None or candidate.experience_min < user_filter.experience_min):
        return False
    if user_filter.experience_max is not None and (candidate.experience_max is None or candidate.experience_max > user_filter.experience_max):
        return False
    if user_filter.company_sizes and candidate.company_size not in user_filter.company_sizes:
        return False
    if user_filter.minimum_employee_count is not None and (
        candidate.employee_count is None or candidate.employee_count < user_filter.minimum_employee_count
    ):
        return False
    return True


def ingest_candidates_for_active_filters(database: Session, candidates: list[JobCandidate]) -> int:
    filters = list(database.scalars(select(UserFilter).where(UserFilter.is_active.is_(True))))
    stored_count = 0
    for candidate in candidates:
        matched_filters = [user_filter for user_filter in filters if filter_matches_candidate(user_filter, candidate)]
        if not matched_filters:
            continue
        job = ingest_candidate(database, candidate)
        database.flush()
        for user_filter in matched_filters:
            existing_match = database.scalar(
                select(JobMatch.id).where(
                    JobMatch.user_id == user_filter.user_id,
                    JobMatch.job_id == job.id,
                    JobMatch.filter_id == user_filter.id,
                )
            )
            if existing_match is None:
                database.add(JobMatch(user_id=user_filter.user_id, job_id=job.id, filter_id=user_filter.id))
        stored_count += 1
    database.commit()
    return stored_count
