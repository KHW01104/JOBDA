from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "JOBDA"
    database_url: str = "postgresql+psycopg://jobda:jobda@postgres:5432/jobda"
    jwt_secret: str = "change-this-secret"
    jwt_access_expire_minutes: int = 30
    admin_username: str = "admin"
    admin_password: str = "change-me"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
