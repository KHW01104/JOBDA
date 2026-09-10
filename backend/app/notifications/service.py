import json
import logging
from datetime import datetime, timezone

from pywebpush import WebPushException, webpush
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Job, JobScrap, NotificationEvent, PushSubscription

logger = logging.getLogger(__name__)

_FIELD_LABELS = {
    "title": "공고명",
    "experience": "경력",
    "employment_type": "고용형태",
    "location": "근무지역",
    "deadline": "마감일",
    "status": "공고 상태",
}


def change_summary(field_changes: dict[str, dict[str, str | None]]) -> str:
    field, values = next(iter(field_changes.items()))
    label = _FIELD_LABELS[field]
    return f"{label} {values['before'] or '-'} → {values['after'] or '-'}"


def send_event(database: Session, event: NotificationEvent) -> None:
    settings = get_settings()
    if not settings.vapid_private_key or not settings.vapid_contact_email:
        return
    subscriptions = database.scalars(select(PushSubscription).where(PushSubscription.user_id == event.user_id))
    payload = json.dumps({"title": event.title, "body": event.body, "job_id": event.job_id}, ensure_ascii=False)
    sent = False
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": f"mailto:{settings.vapid_contact_email}"},
            )
            subscription.last_used_at = datetime.now(timezone.utc)
            sent = True
        except WebPushException as error:
            logger.warning("push delivery failed subscription_id=%s error=%s", subscription.id, error)
    if sent:
        event.sent_at = datetime.now(timezone.utc)


def record_scrap_change_events(
    database: Session,
    job: Job,
    field_changes: dict[str, dict[str, str | None]],
) -> list[NotificationEvent]:
    events: list[NotificationEvent] = []
    scraps = database.scalars(select(JobScrap).where(JobScrap.job_id == job.id))
    for scrap in scraps:
        event = NotificationEvent(
            user_id=scrap.user_id,
            type="WATCHED_JOB_CHANGED",
            job_id=job.id,
            company_id=job.company_id,
            title="스크랩 공고 변경",
            body=f"{job.title}\n{change_summary(field_changes)}",
        )
        database.add(event)
        events.append(event)
    database.flush()
    for event in events:
        send_event(database, event)
    return events
