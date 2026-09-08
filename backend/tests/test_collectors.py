import unittest

from app.collectors.alio import AlioCollector
from app.collectors.saramin import SaraminCollector
from app.jobs.normalizer import normalize_candidate


class CollectorMappingTests(unittest.TestCase):
    def test_saramin_mapping_and_normalization(self) -> None:
        candidate = SaraminCollector.to_candidate(
            {
                "id": "saramin-1",
                "position": {
                    "title": "  백엔드 개발자  ",
                    "experience": "신입",
                    "job-type": "정규직",
                    "location": "서울",
                },
                "company": {"name": " JOBDA "},
                "expiration-date": "2099-12-31",
            }
        )

        normalized = normalize_candidate(candidate)
        self.assertEqual(normalized.company, "JOBDA")
        self.assertEqual(normalized.title, "백엔드 개발자")
        self.assertEqual(normalized.status, "OPEN")
        self.assertEqual(normalized.source_job_id, "saramin-1")

    def test_alio_mapping(self) -> None:
        candidate = AlioCollector.to_candidate(
            {
                "기관명": "공공기관",
                "채용제목": "개발자",
                "공고번호": "alio-1",
                "채용종료일": "2099.12.31",
            }
        )

        self.assertEqual(candidate.company, "공공기관")
        self.assertEqual(candidate.source.value, "ALIO")
        self.assertEqual(candidate.source_job_id, "alio-1")


if __name__ == "__main__":
    unittest.main()
