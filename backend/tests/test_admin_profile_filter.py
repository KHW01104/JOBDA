import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.api.admin import upsert_profile_filter
from app.database import Base
from app.models import User, UserFilter, UserRole
from app.schemas.personalization import UserFilterCreate


class AdminProfileFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_upserts_named_profile_filter_for_target_user(self) -> None:
        with Session(self.engine) as database:
            admin = User(username="admin", password_hash="hash", display_name="관리자", role=UserRole.ADMIN)
            target = User(username="electric", password_hash="hash", display_name="전기", role=UserRole.USER)
            database.add_all([admin, target])
            database.commit()

            created = upsert_profile_filter(
                "electric",
                UserFilterCreate(name="프로필 분석 조건", included_keywords=["전기"], locations=["서울"]),
                database,
                admin,
            )
            updated = upsert_profile_filter(
                "electric",
                UserFilterCreate(name="프로필 분석 조건", included_keywords=["전기", "설비"], locations=["경기"]),
                database,
                admin,
            )
            filters = list(database.scalars(select(UserFilter).where(UserFilter.user_id == target.id)))

        self.assertEqual(created.id, updated.id)
        self.assertEqual(len(filters), 1)
        self.assertEqual(filters[0].included_keywords, ["전기", "설비"])
        self.assertEqual(filters[0].locations, ["경기"])


if __name__ == "__main__":
    unittest.main()
