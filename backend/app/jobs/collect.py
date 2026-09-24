import logging

from sqlalchemy import func, select

from app.collectors import AlioCollector, NaverMailCollector
from app.config import get_settings
from app.database import SessionLocal
from app.jobs.ingest import ingest_candidates_for_active_filters
from app.models import ProcessedMail, UserFilter
from app.models import RecruitmentSchedule
from app.schedules import RecruitmentScheduleCandidate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
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
        mailboxes = NaverMailCollector.mailbox_names(get_settings().naver_imap_mailbox)
        processed_mail_keys = set(
            database.execute(
                select(ProcessedMail.mailbox, ProcessedMail.remote_id).where(
                    ProcessedMail.provider == "NAVER",
                    ProcessedMail.mailbox.in_(mailboxes),
                )
            ).tuples()
        )
    for collector in (NaverMailCollector(processed_mail_keys=processed_mail_keys), AlioCollector()):
        try:
            result = collector.collect()
            if result.error:
                logger.error("source=%s failed=%s", result.source, result.error)
                continue
            with SessionLocal() as database:
                total += ingest_candidates_for_active_filters(database, result.candidates)
                total += ingest_recruitment_schedules(database, result.schedules)
                record_processed_mails(database, result.candidates, result.schedules)
            logger.info("source=%s requested_count=%s new_count=%s", result.source, result.requested_count, result.new_count)
        finally:
            collector.close()
    logger.info("collection completed total_count=%s", total)
    return total


def ingest_recruitment_schedules(database, schedules: list[RecruitmentScheduleCandidate]) -> int:
    stored_count = 0
    for schedule in schedules:
        if database.scalar(select(RecruitmentSchedule.id).where(RecruitmentSchedule.mail_remote_id == schedule.mail_remote_id)) is None:
            database.add(
                RecruitmentSchedule(
                    title=schedule.title,
                    period_start=schedule.period_start,
                    period_end=schedule.period_end,
                    source_name=schedule.source_name,
                    mail_remote_id=schedule.mail_remote_id,
                )
            )
            stored_count += 1
    database.commit()
    return stored_count


def record_processed_mails(database, candidates, schedules: list[RecruitmentScheduleCandidate] = ()) -> None:
    recorded_keys: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        metadata = candidate.raw_metadata or {}
        provider = metadata.get("mail_provider")
        mailbox = metadata.get("mailbox")
        remote_id = metadata.get("mail_key")
        if not provider or not mailbox or not remote_id:
            continue
        key = (provider, mailbox, remote_id)
        if key in recorded_keys:
            continue
        recorded_keys.add(key)
        already_processed = database.scalar(
            select(ProcessedMail.id).where(
                ProcessedMail.provider == key[0],
                ProcessedMail.mailbox == key[1],
                ProcessedMail.remote_id == key[2],
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
    for schedule in schedules:
        provider, mailbox, remote_id = "NAVER", schedule.mailbox, schedule.mail_remote_id
        key = (provider, mailbox, remote_id)
        if key in recorded_keys:
            continue
        recorded_keys.add(key)
        if database.scalar(select(ProcessedMail.id).where(ProcessedMail.provider == provider, ProcessedMail.mailbox == mailbox, ProcessedMail.remote_id == remote_id)) is None:
            database.add(ProcessedMail(provider=provider, mailbox=mailbox, remote_id=remote_id))
    database.commit()


if __name__ == "__main__":
    run()
