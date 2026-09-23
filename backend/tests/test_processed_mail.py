import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.jobs.candidate import CandidateSource, JobCandidate
from app.jobs.collect import record_processed_mails
from app.models import ProcessedMail


class ProcessedMailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_completed_mail_is_recorded_once(self) -> None:
        candidate = JobCandidate(
            company="JOBDA",
            title="백엔드 개발자",
            source=CandidateSource.SARAMIN,
            source_job_id="12345",
            raw_metadata={
                "mail_provider": "NAVER",
                "mailbox": "INBOX",
                "mail_key": "99:1",
                "message_id": "<saramin-1@example.com>",
            },
        )
        with Session(self.engine) as database:
            record_processed_mails(database, [candidate])
            record_processed_mails(database, [candidate])
            mails = list(database.scalars(select(ProcessedMail)))

        self.assertEqual(len(mails), 1)
        self.assertEqual(mails[0].remote_id, "99:1")

    def test_multiple_candidates_from_one_mail_are_recorded_once(self) -> None:
        metadata = {
            "mail_provider": "NAVER",
            "mailbox": "INBOX",
            "mail_key": "99:2",
            "message_id": "<saramin-2@example.com>",
        }
        candidates = [
            JobCandidate(company="JOBDA", title="백엔드 개발자", source=CandidateSource.SARAMIN, source_job_id="12346", raw_metadata=metadata),
            JobCandidate(company="JOBDA", title="플랫폼 개발자", source=CandidateSource.SARAMIN, source_job_id="12347", raw_metadata=metadata),
        ]
        with Session(self.engine) as database:
            record_processed_mails(database, candidates)
            mails = list(database.scalars(select(ProcessedMail)))

        self.assertEqual(len(mails), 1)
        self.assertEqual(mails[0].remote_id, "99:2")


if __name__ == "__main__":
    unittest.main()
