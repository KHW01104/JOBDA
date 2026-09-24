from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RecruitmentSchedule, User
from app.schemas.schedules import RecruitmentScheduleResponse
from app.security.auth import get_current_user

router = APIRouter(prefix="/recruitment-schedules", tags=["공채 일정"])


@router.get("", response_model=list[RecruitmentScheduleResponse])
def list_recruitment_schedules(
    database: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[RecruitmentSchedule]:
    return list(database.scalars(select(RecruitmentSchedule).where(RecruitmentSchedule.period_end >= date.today()).order_by(RecruitmentSchedule.period_start)))
