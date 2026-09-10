import json
from hashlib import sha256

from app.jobs.candidate import JobCandidate
from app.models import JobVersion


def experience_value(candidate: JobCandidate) -> str | None:
    if candidate.experience_min is not None or candidate.experience_max is not None:
        minimum = str(candidate.experience_min) if candidate.experience_min is not None else ""
        maximum = str(candidate.experience_max) if candidate.experience_max is not None else ""
        return f"{minimum}~{maximum}년"
    return candidate.experience_type


def candidate_snapshot(candidate: JobCandidate) -> dict[str, str | None]:
    return {
        "title": candidate.title,
        "experience": experience_value(candidate),
        "employment_type": candidate.employment_type,
        "location": candidate.location,
        "deadline": candidate.deadline.isoformat() if candidate.deadline else None,
        "status": candidate.status,
    }


def version_snapshot(version: JobVersion) -> dict[str, str | None]:
    return {
        "title": version.title,
        "experience": version.experience,
        "employment_type": version.employment_type,
        "location": version.location,
        "deadline": version.deadline.isoformat() if version.deadline else None,
        "status": version.status.value,
    }


def content_hash(candidate: JobCandidate) -> str:
    payload = json.dumps(candidate_snapshot(candidate), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode()).hexdigest()


def changed_fields(previous_version: JobVersion, candidate: JobCandidate) -> dict[str, dict[str, str | None]]:
    previous = version_snapshot(previous_version)
    current = candidate_snapshot(candidate)
    return {
        field: {"before": previous[field], "after": current[field]}
        for field in current
        if previous[field] != current[field]
    }
