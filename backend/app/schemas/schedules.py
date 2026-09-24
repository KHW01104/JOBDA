from datetime import date

from pydantic import BaseModel


class RecruitmentScheduleResponse(BaseModel):
    id: int
    source_name: str
    title: str
    period_start: date
    period_end: date

    class Config:
        from_attributes = True
