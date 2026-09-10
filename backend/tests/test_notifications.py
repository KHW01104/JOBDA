from datetime import date
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.jobs.candidate import CandidateSource, JobCandidate
from app.jobs.ingest import ingest_candidates
from app.models import Job, JobScrap, NotificationEvent, User, UserRole


def candidate(**changes: object) -> JobCandidate:
    values = {
        "company": "JOBDA", "title": "백엔드 개발자", "location": "서울", "employment_type": "정규직",
        "deadline": date(2099, 12, 31), "status": "OPEN", "source": CandidateSource.SARAMIN, "source_job_id": "saramin-1",
    }
    values.update(changes)
    return JobCandidate(**values)


class NotificationTests(unittest.TestCase):
    def test_scrap_change_creates_notification_event(self) -> None:
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as database:
            user = User(username="user", password_hash="hash", display_name="사용자", role=UserRole.USER)
            database.add(user)
            ingest_candidates(database, [candidate()])
            job = database.scalar(select(Job))
            database.add(JobScrap(user_id=user.id, job_id=job.id))
            database.commit()
            ingest_candidates(database, [candidate(deadline=date(2100, 1, 31))])
            events = list(database.scalars(select(NotificationEvent)))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, "WATCHED_JOB_CHANGED")
        self.assertIn("마감일", events[0].body)
        engine.dispose()


if __name__ == "__main__":
    unittest.main()
