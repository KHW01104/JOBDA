from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api import admin, auth, jobs
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import User, UserRole
from app.security.auth import hash_password


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    database = SessionLocal()
    try:
        settings = get_settings()
        if database.scalar(select(User).where(User.username == settings.admin_username)) is None:
            database.add(
                User(
                    username=settings.admin_username,
                    password_hash=hash_password(settings.admin_password),
                    display_name="관리자",
                    role=UserRole.ADMIN,
                    must_change_password=False,
                )
            )
            database.commit()
    finally:
        database.close()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
