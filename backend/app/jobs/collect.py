import logging

from sqlalchemy import func, select

from app.collectors import AlioCollector, NaverMailCollector
from app.config import get_settings
from app.database import SessionLocal
from app.jobs.ingest import ingest_candidates_for_active_filters
from app.models import ProcessedMail, UserFilter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run() -> int:
    total = 0
    with SessionLocal() as database:
        active_filter_count = database.scalar(
            select(func.count()).select_from(UserFilter).where(UserFilter.is_active.is_(True))
        )
        if not active_filter_count:
            logger.info("collection skipped because no active user filters exist")
            return total
        mailbox = get_settings().naver_imap_mailbox
        processed_mail_keys = set(
            database.scalars(
                select(ProcessedMail.remote_id).where(
                    ProcessedMail.provider == "NAVER",
                    ProcessedMail.mailbox == mailbox,
                )
            )
        )
    for collector in (NaverMailCollector(processed_mail_keys=processed_mail_keys), AlioCollector()):
        try:
            result = collector.collect()
            if result.error:
                logger.error("source=%s failed=%s", result.source, result.error)
                continue
            with SessionLocal() as database:
                total += ingest_candidates_for_active_filters(database, result.candidates)
                record_processed_mails(database, result.candidates)
            logger.info("source=%s requested_count=%s new_count=%s", result.source, result.requested_count, result.new_count)
        finally:
            collector.close()
    logger.info("collection completed total_count=%s", total)
    return total


def record_processed_mails(database, candidates) -> None:
    for candidate in candidates:
        metadata = candidate.raw_metadata or {}
        provider = metadata.get("mail_provider")
        mailbox = metadata.get("mailbox")
        remote_id = metadata.get("mail_key")
        if not provider or not mailbox or not remote_id:
            continue
        already_processed = database.scalar(
            select(ProcessedMail.id).where(
                ProcessedMail.provider == provider,
                ProcessedMail.mailbox == mailbox,
                ProcessedMail.remote_id == remote_id,
            )
        )
        if already_processed is None:
            database.add(
                ProcessedMail(
                    provider=provider,
                    mailbox=mailbox,
                    remote_id=remote_id,
                    message_id=metadata.get("message_id"),
                )
            )
    database.commit()


if __name__ == "__main__":
    run()
