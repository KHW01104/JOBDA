import unittest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database import Base
from app.models import User, UserFilter, UserRole
from app.security.auth import hash_password


class PersonalizationOwnershipTests(unittest.TestCase):
    def test_filters_are_scoped_to_owner(self) -> None:
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as database:
            first_user = User(username="first", password_hash=hash_password("password"), display_name="첫 사용자", role=UserRole.USER)
            second_user = User(username="second", password_hash=hash_password("password"), display_name="둘째 사용자", role=UserRole.USER)
            database.add_all([first_user, second_user])
            database.flush()
            database.add(UserFilter(user_id=first_user.id, name="백엔드 신입", job_categories=["Backend"]))
            database.commit()

            first_filters = list(database.scalars(select(UserFilter).where(UserFilter.user_id == first_user.id)))
            second_filters = list(database.scalars(select(UserFilter).where(UserFilter.user_id == second_user.id)))

        self.assertEqual(len(first_filters), 1)
        self.assertEqual(second_filters, [])


if __name__ == "__main__":
    unittest.main()
