from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RecruitmentScheduleCandidate:
    title: str
    period_start: date
    period_end: date
    source_name: str
    mail_remote_id: str
    mailbox: str
