import logging

from app.collectors import AlioCollector, SaraminCollector
from app.database import SessionLocal
from app.jobs.ingest import ingest_candidates

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run() -> int:
    total = 0
    for collector in (SaraminCollector(), AlioCollector()):
        try:
            result = collector.collect()
            if result.error:
                logger.error("source=%s failed=%s", result.source, result.error)
                continue
            with SessionLocal() as database:
                total += ingest_candidates(database, result.candidates)
            logger.info("source=%s requested_count=%s new_count=%s", result.source, result.requested_count, result.new_count)
        finally:
            collector.close()
    logger.info("collection completed total_count=%s", total)
    return total


if __name__ == "__main__":
    run()
