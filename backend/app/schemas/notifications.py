from datetime import datetime

from pydantic import BaseModel, Field


class PushSubscriptionCreate(BaseModel):
    endpoint: str = Field(min_length=1)
    p256dh: str = Field(min_length=1, max_length=512)
    auth: str = Field(min_length=1, max_length=512)
    user_agent: str | None = Field(default=None, max_length=500)


class PushSubscriptionResponse(PushSubscriptionCreate):
    id: int

    class Config:
        from_attributes = True


class NotificationEventResponse(BaseModel):
    id: int
    type: str
    job_id: int | None
    company_id: int | None
    title: str
    body: str
    is_read: bool
    sent_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
