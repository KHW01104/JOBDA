import re
from datetime import date

from app.jobs.candidate import JobCandidate
from app.models import CompanyType, JobStatus


_WHITESPACE = re.compile(r"\\s+")


def normalize_text(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def normalize_name(value: str) -> str:
    return normalize_text(value).casefold()


def parse_status(value: str | None, deadline: date | None) -> JobStatus:
    normalized = normalize_text(value or "").casefold()
    if normalized in {"closed", "마감", "종료", "채용종료"}:
        return JobStatus.CLOSED
    if normalized in {"open", "진행중", "채용중", "접수중"}:
        return JobStatus.OPEN
    if deadline is not None:
        return JobStatus.CLOSED if deadline < date.today() else JobStatus.OPEN
    return JobStatus.UNKNOWN


def normalize_candidate(candidate: JobCandidate) -> JobCandidate:
    return candidate.model_copy(
        update={
            "company": normalize_text(candidate.company),
            "title": normalize_text(candidate.title),
            "job_category": normalize_text(candidate.job_category) if candidate.job_category else None,
            "employment_type": normalize_text(candidate.employment_type) if candidate.employment_type else None,
            "location": normalize_text(candidate.location) if candidate.location else None,
            "education": normalize_text(candidate.education) if candidate.education else None,
            "status": parse_status(candidate.status, candidate.deadline).value,
        }
    )


def company_defaults(candidate: JobCandidate) -> dict[str, str]:
    return {
        "name": candidate.company,
        "normalized_name": normalize_name(candidate.company),
        "company_type": CompanyType.PUBLIC.value if candidate.source.value == "ALIO" else CompanyType.PRIVATE.value,
    }
