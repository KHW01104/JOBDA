from datetime import date
from typing import Any

from app.collectors.base import Collector
from app.config import get_settings
from app.jobs.candidate import CandidateSource, JobCandidate


class AlioCollector(Collector):
    source = CandidateSource.ALIO.value

    def __init__(self, client=None, api_key: str | None = None, endpoint: str | None = None) -> None:
        super().__init__(client)
        settings = get_settings()
        self.api_key = api_key or settings.alio_api_key
        self.endpoint = endpoint or settings.alio_api_url

    def fetch_candidates(self) -> list[JobCandidate]:
        if not self.api_key:
            raise ValueError("ALIO_API_KEY가 설정되지 않았습니다.")
        response = self.client.get(self.endpoint, params={"apiKey": self.api_key, "pageNo": 1, "numOfRows": 100})
        response.raise_for_status()
        payload = response.json()
        items = payload.get("items", payload.get("data", []))
        return [self.to_candidate(item) for item in items]

    @staticmethod
    def to_candidate(item: dict[str, Any]) -> JobCandidate:
        return JobCandidate(
            company=str(item.get("기관명") or item.get("companyName") or item.get("orgName") or "알 수 없는 기관"),
            title=str(item.get("채용제목") or item.get("title") or "제목 없음"),
            job_category=item.get("채용분야") or item.get("jobCategory"),
            location=item.get("근무지") or item.get("location"),
            education=item.get("필요학력") or item.get("education"),
            employment_type=item.get("고용형태") or item.get("employmentType"),
            experience_type=item.get("경력구분") or item.get("experienceType"),
            deadline=AlioCollector.parse_date(item.get("채용종료일") or item.get("endDate")),
            status=item.get("채용상태") or item.get("status"),
            source=CandidateSource.ALIO,
            source_job_id=str(item.get("공고번호") or item.get("seq") or item.get("id") or ""),
            source_url=item.get("원본 공고 URL") or item.get("url"),
            raw_metadata=item,
        )

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(str(value)[:10].replace(".", "-"))
