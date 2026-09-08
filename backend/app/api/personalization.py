from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CompanyWatch, JobScrap, User, UserFilter
from app.schemas.personalization import (
    CompanyWatchCreate,
    CompanyWatchResponse,
    JobScrapCreate,
    JobScrapResponse,
    UserFilterCreate,
    UserFilterResponse,
)
from app.security.auth import get_current_user

router = APIRouter(prefix="/personalization", tags=["개인화"])


def owned_item(database: Session, model: type, item_id: int, user_id: int):
    return database.scalar(select(model).where(model.id == item_id, model.user_id == user_id))


@router.get("/filters", response_model=list[UserFilterResponse])
def list_filters(database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[UserFilter]:
    return list(database.scalars(select(UserFilter).where(UserFilter.user_id == user.id).order_by(UserFilter.id.desc())))


@router.post("/filters", response_model=UserFilterResponse, status_code=status.HTTP_201_CREATED)
def create_filter(payload: UserFilterCreate, database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> UserFilter:
    user_filter = UserFilter(user_id=user.id, **payload.model_dump())
    database.add(user_filter)
    database.commit()
    database.refresh(user_filter)
    return user_filter


@router.delete("/filters/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_filter(filter_id: int, database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    user_filter = owned_item(database, UserFilter, filter_id, user.id)
    if user_filter is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="필터를 찾을 수 없습니다.")
    database.delete(user_filter)
    database.commit()


@router.get("/watches", response_model=list[CompanyWatchResponse])
def list_watches(database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[CompanyWatch]:
    return list(database.scalars(select(CompanyWatch).where(CompanyWatch.user_id == user.id).order_by(CompanyWatch.id.desc())))


@router.post("/watches", response_model=CompanyWatchResponse, status_code=status.HTTP_201_CREATED)
def create_watch(payload: CompanyWatchCreate, database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CompanyWatch:
    watch = CompanyWatch(user_id=user.id, **payload.model_dump())
    database.add(watch)
    database.commit()
    database.refresh(watch)
    return watch


@router.delete("/watches/{watch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watch(watch_id: int, database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    watch = owned_item(database, CompanyWatch, watch_id, user.id)
    if watch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="관심기업을 찾을 수 없습니다.")
    database.delete(watch)
    database.commit()


@router.get("/scraps", response_model=list[JobScrapResponse])
def list_scraps(database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[JobScrap]:
    return list(database.scalars(select(JobScrap).where(JobScrap.user_id == user.id).order_by(JobScrap.id.desc())))


@router.post("/scraps", response_model=JobScrapResponse, status_code=status.HTTP_201_CREATED)
def create_scrap(payload: JobScrapCreate, database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> JobScrap:
    scrap = JobScrap(user_id=user.id, **payload.model_dump())
    database.add(scrap)
    database.commit()
    database.refresh(scrap)
    return scrap


@router.delete("/scraps/{scrap_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scrap(scrap_id: int, database: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    scrap = owned_item(database, JobScrap, scrap_id, user.id)
    if scrap is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="스크랩을 찾을 수 없습니다.")
    database.delete(scrap)
    database.commit()
