"""Application settings.

DATABASE_URL defaults to a local SQLite file so the backend runs without
any external services. Point it at Postgres in production, e.g.:
DATABASE_URL=postgresql://user:password@localhost:5432/finpilot
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./backend/finpilot.db"
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
