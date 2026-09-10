from datetime import date
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.jobs.candidate import CandidateSource, JobCandidate
from app.jobs.ingest import ingest_candidates
from app.models import Job, JobSource


def candidate(source: CandidateSource, source_job_id: str, **changes: object) -> JobCandidate:
    values = {
        "company": "JOBDA",
        "title": "백엔드 개발자",
        "location": "서울",
        "employment_type": "정규직",
        "deadline": date(2099, 12, 31),
        "status": "OPEN",
        "source": source,
        "source_job_id": source_job_id,
    }
    values.update(changes)
    return JobCandidate(**values)


class DeduplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_same_job_from_different_sources_is_merged(self) -> None:
        with Session(self.engine) as database:
            ingest_candidates(
                database,
                [
                    candidate(CandidateSource.SARAMIN, "saramin-1"),
                    candidate(CandidateSource.ALIO, "alio-1", company=" jobda ", title="  백엔드 개발자  "),
                ],
            )
            jobs = list(database.scalars(select(Job)))
            sources = list(database.scalars(select(JobSource)))

        self.assertEqual(len(jobs), 1)
        self.assertEqual(len(sources), 2)
        self.assertEqual({source.job_id for source in sources}, {jobs[0].id})

    def test_same_source_is_updated_without_another_source_row(self) -> None:
        with Session(self.engine) as database:
            ingest_candidates(database, [candidate(CandidateSource.SARAMIN, "saramin-1")])
            ingest_candidates(
                database,
                [candidate(CandidateSource.SARAMIN, "saramin-1", title="백엔드 플랫폼 개발자")],
            )
            jobs = list(database.scalars(select(Job)))
            sources = list(database.scalars(select(JobSource)))

        self.assertEqual(len(jobs), 1)
        self.assertEqual(len(sources), 1)
        self.assertEqual(jobs[0].title, "백엔드 플랫폼 개발자")

    def test_incomplete_candidate_is_not_merged(self) -> None:
        with Session(self.engine) as database:
            ingest_candidates(
                database,
                [
                    candidate(CandidateSource.SARAMIN, "saramin-1", deadline=None),
                    candidate(CandidateSource.ALIO, "alio-1", deadline=None),
                ],
            )
            jobs = list(database.scalars(select(Job)))

        self.assertEqual(len(jobs), 2)


if __name__ == "__main__":
    unittest.main()
