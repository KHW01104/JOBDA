from datetime import date
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.jobs.candidate import CandidateSource, JobCandidate
from app.jobs.ingest import ingest_candidates
from app.models import JobVersion


def candidate(**changes: object) -> JobCandidate:
    values = {
        "company": "JOBDA",
        "title": "백엔드 개발자",
        "experience_type": "신입",
        "location": "서울",
        "employment_type": "정규직",
        "deadline": date(2099, 12, 31),
        "status": "OPEN",
        "source": CandidateSource.SARAMIN,
        "source_job_id": "saramin-1",
    }
    values.update(changes)
    return JobCandidate(**values)


class ChangeDetectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_changed_deadline_creates_a_version_with_field_changes(self) -> None:
        with Session(self.engine) as database:
            ingest_candidates(database, [candidate()])
            ingest_candidates(database, [candidate(deadline=date(2100, 1, 31))])
            versions = list(database.scalars(select(JobVersion).order_by(JobVersion.version)))

        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[1].version, 2)
        self.assertEqual(
            versions[1].field_changes,
            {"deadline": {"before": "2099-12-31", "after": "2100-01-31"}},
        )

    def test_unchanged_candidate_does_not_create_another_version(self) -> None:
        with Session(self.engine) as database:
            ingest_candidates(database, [candidate()])
            ingest_candidates(database, [candidate()])
            versions = list(database.scalars(select(JobVersion)))

        self.assertEqual(len(versions), 1)


if __name__ == "__main__":
    unittest.main()
