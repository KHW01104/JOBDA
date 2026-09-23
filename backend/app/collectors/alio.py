from datetime import date
from typing import Any

from app.collectors.base import Collector
from app.config import get_settings
from app.jobs.candidate import CandidateSource, JobCandidate


class AlioCollector(Collector):
    source = CandidateSource.ALIO.value

    def __init__(
        self,
        client=None,
        api_key: str | None = None,
        endpoint: str | None = None,
        detail_endpoint: str | None = None,
        page_size: int | None = None,
    ) -> None:
        super().__init__(client)
        settings = get_settings()
        self.api_key = api_key or settings.alio_api_key
        self.endpoint = endpoint or settings.alio_api_url
        self.detail_endpoint = detail_endpoint or settings.alio_api_detail_url
        self.page_size = page_size or settings.alio_api_page_size

    def fetch_candidates(self) -> list[JobCandidate]:
        if not self.api_key:
            raise ValueError("ALIO_API_KEY가 설정되지 않았습니다.")
        if self.page_size < 1:
            raise ValueError("ALIO_API_PAGE_SIZE는 1 이상이어야 합니다.")

        candidates: list[JobCandidate] = []
        page_no = 1
        total_count = 0
        while True:
            payload = self.request_payload(
                self.endpoint,
                {
                    "ongoingYn": "Y",
                    "pageNo": page_no,
                    "numOfRows": self.page_size,
                },
            )
            items = payload.get("result", [])
            if not isinstance(items, list):
                raise ValueError("ALIO API 응답의 공고 목록 형식이 올바르지 않습니다.")
            for item in items:
                if not isinstance(item, dict):
                    continue
                candidates.append(self.to_candidate({**item, **self.fetch_detail(item)}))

            total_count = self.parse_total_count(payload.get("totalCount"))
            if not items or page_no * self.page_size >= total_count:
                break
            page_no += 1
        return candidates

    def fetch_detail(self, item: dict[str, Any]) -> dict[str, Any]:
        announcement_id = item.get("recrutPblntSn")
        if announcement_id in (None, ""):
            return {}
        payload = self.request_payload(self.detail_endpoint, {"sn": announcement_id})
        result = payload.get("result", {})
        if not isinstance(result, dict):
            raise ValueError("ALIO API 응답의 공고 상세 형식이 올바르지 않습니다.")
        return result

    def request_payload(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.client.post(
            endpoint,
            params={"serviceKey": self.api_key, "resultType": "json", **params},
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("ALIO API 응답 형식이 올바르지 않습니다.")
        if str(payload.get("resultCode")) not in {"0", "200"}:
            raise ValueError(f"ALIO API 요청에 실패했습니다: {payload.get('resultMsg') or '알 수 없는 오류'}")
        return payload

    @staticmethod
    def parse_total_count(value: Any) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def to_candidate(item: dict[str, Any]) -> JobCandidate:
        return JobCandidate(
            company=str(item.get("instNm") or "알 수 없는 기관"),
            title=str(item.get("recrutPbancTtl") or "제목 없음"),
            job_category=item.get("ncsCdNmLst"),
            location=item.get("workRgnNmLst"),
            education=item.get("acbgCondNmLst"),
            employment_type=item.get("hireTypeNmLst"),
            experience_type=item.get("recrutSeNm"),
            deadline=AlioCollector.parse_date(item.get("pbancEndYmd")),
            status="진행중" if item.get("ongoingYn") == "Y" else "마감",
            company_size="공공기관",
            source=CandidateSource.ALIO,
            source_job_id=str(item.get("recrutPblntSn") or ""),
            source_url=item.get("srcUrl"),
            raw_metadata=item,
        )

    @staticmethod
    def parse_date(value: str | None) -> date | None:
        if not value:
            return None
        return date.fromisoformat(str(value)[:10].replace(".", "-"))
