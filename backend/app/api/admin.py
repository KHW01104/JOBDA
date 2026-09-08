from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas.auth import CreateUserRequest, UserResponse
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
