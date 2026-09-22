from datetime import date
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.jobs.candidate import CandidateSource, JobCandidate
from app.jobs.ingest import ingest_candidates_for_active_filters
from app.models import Job, JobMatch, User, UserFilter, UserRole


def candidate(title: str, source_job_id: str) -> JobCandidate:
    return JobCandidate(
        company="JOBDA",
        title=title,
        deadline=date(2099, 12, 31),
        status="OPEN",
        source=CandidateSource.SARAMIN,
        source_job_id=source_job_id,
    )


class JobMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_only_matching_user_filters_store_and_link_jobs(self) -> None:
        with Session(self.engine) as database:
            developer = User(username="developer", password_hash="hash", display_name="개발자", role=UserRole.USER)
            electrician = User(username="electrician", password_hash="hash", display_name="전기", role=UserRole.USER)
            database.add_all([developer, electrician])
            database.flush()
            database.add_all([
                UserFilter(user_id=developer.id, name="개발", included_keywords=["개발"]),
                UserFilter(user_id=electrician.id, name="전기", included_keywords=["전기"]),
            ])
            user_ids = {developer.id, electrician.id}
            database.commit()

            stored = ingest_candidates_for_active_filters(database, [
                candidate("백엔드 개발자", "job-1"),
                candidate("전기 설비 기사", "job-2"),
                candidate("회계 담당자", "job-3"),
            ])
            jobs = list(database.scalars(select(Job)))
            matches = list(database.scalars(select(JobMatch)))

        self.assertEqual(stored, 2)
        self.assertEqual(len(jobs), 2)
        self.assertEqual({match.user_id for match in matches}, user_ids)


if __name__ == "__main__":
    unittest.main()
