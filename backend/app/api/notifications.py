from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NotificationEvent, PushSubscription, User
from app.schemas.notifications import NotificationEventResponse, PushSubscriptionCreate, PushSubscriptionResponse
from app.security.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["알림"])


@router.get("/subscriptions", response_model=list[PushSubscriptionResponse])
def list_subscriptions(database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[PushSubscription]:
    return list(database.scalars(select(PushSubscription).where(PushSubscription.user_id == user.id)))


@router.post("/subscriptions", response_model=PushSubscriptionResponse, status_code=status.HTTP_201_CREATED)
def create_subscription(
    payload: PushSubscriptionCreate,
    database: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PushSubscription:
    subscription = database.scalar(
        select(PushSubscription).where(PushSubscription.user_id == user.id, PushSubscription.endpoint == payload.endpoint)
    )
    if subscription is None:
        subscription = PushSubscription(user_id=user.id, **payload.model_dump())
        database.add(subscription)
    else:
        subscription.p256dh = payload.p256dh
        subscription.auth = payload.auth
        subscription.user_agent = payload.user_agent
    database.commit()
    database.refresh(subscription)
    return subscription


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subscription(
    subscription_id: int,
    database: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    subscription = database.scalar(
        select(PushSubscription).where(PushSubscription.id == subscription_id, PushSubscription.user_id == user.id)
    )
    if subscription is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Push 구독을 찾을 수 없습니다.")
    database.delete(subscription)
    database.commit()


@router.get("/events", response_model=list[NotificationEventResponse])
def list_events(database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[NotificationEvent]:
    return list(
        database.scalars(
            select(NotificationEvent)
            .where(NotificationEvent.user_id == user.id)
            .order_by(NotificationEvent.created_at.desc())
        )
    )


@router.post("/events/{event_id}/read", response_model=NotificationEventResponse)
def read_event(
    event_id: int,
    database: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> NotificationEvent:
    event = database.scalar(
        select(NotificationEvent).where(NotificationEvent.id == event_id, NotificationEvent.user_id == user.id)
    )
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
    event.is_read = True
    database.commit()
    database.refresh(event)
    return event
