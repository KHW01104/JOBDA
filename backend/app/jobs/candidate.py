from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class CandidateSource(StrEnum):
    SARAMIN = "SARAMIN"
    ALIO = "ALIO"


class JobCandidate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company: str
    title: str
    job_category: str | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    experience_type: str | None = None
    employment_type: str | None = None
    location: str | None = None
    education: str | None = None
    published_at: datetime | None = None
    deadline: date | None = None
    status: str | None = None
    source: CandidateSource
    source_job_id: str
    source_url: str | None = None
    raw_metadata: dict | None = None
