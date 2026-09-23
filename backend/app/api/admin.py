from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.jobs.ingest import reconcile_filter_matches
from app.models import User, UserFilter, UserRole
from app.schemas.auth import CreateUserRequest, UserResponse
from app.schemas.personalization import UserFilterCreate, UserFilterResponse
from app.security.auth import hash_password, require_admin

router = APIRouter(prefix="/admin", tags=["관리자"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    database: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> User:
    if database.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 아이디입니다.")

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role=UserRole.USER,
    )
    database.add(user)
    database.commit()
    database.refresh(user)
    return user


@router.put("/users/{username}/profile-filter", response_model=UserFilterResponse)
def upsert_profile_filter(
    username: str,
    payload: UserFilterCreate,
    database: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserFilter:
    user = database.scalar(select(User).where(User.username == username))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

    user_filter = database.scalar(
        select(UserFilter).where(UserFilter.user_id == user.id, UserFilter.name == payload.name)
    )
    if user_filter is None:
        user_filter = UserFilter(user_id=user.id, **payload.model_dump())
        database.add(user_filter)
    else:
        for field, value in payload.model_dump().items():
            setattr(user_filter, field, value)
    database.flush()
    reconcile_filter_matches(database, user_filter)
    database.commit()
    database.refresh(user_filter)
    return user_filter
