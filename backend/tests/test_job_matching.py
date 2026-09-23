from datetime import date
import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.jobs.candidate import CandidateSource, JobCandidate
from app.jobs.ingest import ingest_candidates_for_active_filters, reconcile_filter_matches
from app.models import Job, JobMatch, User, UserFilter, UserRole


def candidate(title: str, source_job_id: str, **values) -> JobCandidate:
    return JobCandidate(
        company="JOBDA",
        title=title,
        deadline=date(2099, 12, 31),
        status="OPEN",
        source=CandidateSource.SARAMIN,
        source_job_id=source_job_id,
        **values,
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

    def test_matches_company_size_and_employee_count(self) -> None:
        with Session(self.engine) as database:
            user = User(username="public", password_hash="hash", display_name="공공", role=UserRole.USER)
            database.add(user)
            database.flush()
            database.add(UserFilter(
                user_id=user.id,
                name="공공기관",
                company_sizes=["공공기관"],
                minimum_employee_count=100,
            ))
            database.commit()

            stored = ingest_candidates_for_active_filters(database, [
                candidate("기관 개발자", "public-1", company_size="공공기관", employee_count=200),
                candidate("소규모 개발자", "private-1", company_size="중소", employee_count=20),
            ])

        self.assertEqual(stored, 1)

    def test_matches_entry_level_label_when_years_are_unavailable(self) -> None:
        with Session(self.engine) as database:
            user = User(username="entry", password_hash="hash", display_name="신입", role=UserRole.USER)
            database.add(user)
            database.flush()
            database.add(UserFilter(user_id=user.id, name="신입", experience_max=0))
            database.commit()

            stored = ingest_candidates_for_active_filters(database, [
                candidate("신입 백엔드 개발자", "entry-1", experience_type="신입"),
                candidate("경력 백엔드 개발자", "career-1", experience_type="경력"),
            ])

        self.assertEqual(stored, 1)

    def test_matches_unknown_optional_fields_and_region_alias(self) -> None:
        with Session(self.engine) as database:
            user = User(username="profile", password_hash="hash", display_name="프로필", role=UserRole.USER)
            database.add(user)
            database.flush()
            database.add(UserFilter(
                user_id=user.id,
                name="프로필 조건",
                locations=["서울"],
                experience_max=0,
            ))
            database.commit()

            stored = ingest_candidates_for_active_filters(database, [
                candidate("백엔드 개발자", "mail-1"),
                candidate("서울 개발자", "alio-1", location="서울특별시", experience_type="신입"),
                candidate("경력 개발자", "career-1", location="서울특별시", experience_type="경력"),
            ])

        self.assertEqual(stored, 2)

    def test_excludes_non_developer_role_even_when_it_has_a_matching_keyword(self) -> None:
        with Session(self.engine) as database:
            user = User(username="backend", password_hash="hash", display_name="백엔드", role=UserRole.USER)
            database.add(user)
            database.flush()
            database.add(UserFilter(
                user_id=user.id,
                name="개발 직무",
                included_keywords=["AI", "백엔드"],
                excluded_keywords=["의사", "간호"],
            ))
            database.commit()

            stored = ingest_candidates_for_active_filters(database, [
                candidate("AI 기반 진료 의사", "doctor-1"),
                candidate("AI 백엔드 엔지니어", "engineer-1"),
            ])

        self.assertEqual(stored, 1)

    def test_reconciles_existing_matches_when_filter_becomes_stricter(self) -> None:
        with Session(self.engine) as database:
            user = User(username="reconcile", password_hash="hash", display_name="재판정", role=UserRole.USER)
            database.add(user)
            database.flush()
            user_filter = UserFilter(user_id=user.id, name="프로필", included_keywords=["의료"])
            database.add(user_filter)
            database.commit()

            ingest_candidates_for_active_filters(database, [candidate("의료 연구원", "medical-1")])
            user_filter.included_keywords = ["백엔드"]
            removed = reconcile_filter_matches(database, user_filter)
            database.commit()

            self.assertEqual(removed, 1)
            self.assertEqual(list(database.scalars(select(Job))), [])
            self.assertEqual(list(database.scalars(select(JobMatch))), [])


if __name__ == "__main__":
    unittest.main()
