from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.security.auth import create_access_token, get_current_user, verify_password

router = APIRouter(prefix="/auth", tags=["인증"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, database: Session = Depends(get_db)) -> TokenResponse:
    user = database.scalar(select(User).where(User.username == payload.username))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="아이디 또는 비밀번호가 올바르지 않습니다.")

    user.last_login_at = datetime.now(timezone.utc)
    database.commit()
    return TokenResponse(access_token=create_access_token(user), user=user)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
