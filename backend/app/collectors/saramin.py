from datetime import date, datetime
from typing import Any

from app.collectors.base import Collector
from app.config import get_settings
from app.jobs.candidate import CandidateSource, JobCandidate


class SaraminCollector(Collector):
    source = CandidateSource.SARAMIN.value

    def __init__(self, client=None, api_key: str | None = None, endpoint: str | None = None) -> None:
        super().__init__(client)
        settings = get_settings()
        self.api_key = api_key or settings.saramin_api_key
        self.endpoint = endpoint or settings.saramin_api_url

    def fetch_candidates(self) -> list[JobCandidate]:
        if not self.api_key:
            raise ValueError("SARAMIN_API_KEY가 설정되지 않았습니다.")
        response = self.client.get(self.endpoint, params={"access-token": self.api_key, "job_mid": "0"})
        response.raise_for_status()
        return [self.to_candidate(item) for item in response.json().get("jobs", [])]

    @staticmethod
    def to_candidate(item: dict[str, Any]) -> JobCandidate:
        position = item.get("position", {})
        company = item.get("company", {})
        job = item.get("job", {})
        return JobCandidate(
            company=str(company.get("name") or "알 수 없는 기업"),
            title=str(position.get("title") or item.get("title") or "제목 없음"),
            job_category=position.get("job-category") or position.get("job-type"),
            location=position.get("location"),
            experience_type=position.get("experience"),
            employment_type=position.get("job-type"),
            deadline=SaraminCollector.parse_date(item.get("expiration-date")),
            published_at=SaraminCollector.parse_datetime(item.get("posting-date")),
            source=CandidateSource.SARAMIN,
            source_job_id=str(item.get("id") or job.get("id") or ""),
            source_url=item.get("url"),
            raw_metadata=item,
        )

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(value[:10])

    @staticmethod
    def parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
