from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProcessedMail(Base):
    __tablename__ = "processed_mails"
    __table_args__ = (UniqueConstraint("provider", "mailbox", "remote_id", name="uq_processed_mails_remote"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(30))
    mailbox: Mapped[str] = mapped_column(String(200))
    remote_id: Mapped[str] = mapped_column(String(200))
    message_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
