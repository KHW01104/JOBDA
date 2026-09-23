import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base
from app.jobs.collect import run


class CollectionGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)

    def tearDown(self) -> None:
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_skips_collectors_when_no_active_user_filter_exists(self) -> None:
        with Session(self.engine) as database:
            with patch("app.jobs.collect.SessionLocal", return_value=database), patch("app.jobs.collect.NaverMailCollector") as naver, patch("app.jobs.collect.AlioCollector") as alio:
                total = run()

        self.assertEqual(total, 0)
        naver.assert_not_called()
        alio.assert_not_called()


if __name__ == "__main__":
    unittest.main()
