import unittest

from app.collectors.alio import AlioCollector
from app.collectors.naver_mail import NaverMailCollector


class CollectionIsolationTests(unittest.TestCase):
    def test_missing_credentials_are_reported_per_source(self) -> None:
        saramin = NaverMailCollector(username="", app_password="")
        alio = AlioCollector(api_key="", endpoint="https://example.com")
        try:
            self.assertIsNotNone(saramin.collect().error)
            self.assertIsNotNone(alio.collect().error)
        finally:
            saramin.close()
            alio.close()


if __name__ == "__main__":
    unittest.main()
