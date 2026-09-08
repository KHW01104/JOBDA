import unittest

from app.collectors.alio import AlioCollector
from app.collectors.saramin import SaraminCollector


class CollectionIsolationTests(unittest.TestCase):
    def test_missing_api_key_is_reported_per_source(self) -> None:
        saramin = SaraminCollector(api_key="", endpoint="https://example.com")
        alio = AlioCollector(api_key="", endpoint="https://example.com")
        try:
            self.assertIsNotNone(saramin.collect().error)
            self.assertIsNotNone(alio.collect().error)
        finally:
            saramin.close()
            alio.close()


if __name__ == "__main__":
    unittest.main()
