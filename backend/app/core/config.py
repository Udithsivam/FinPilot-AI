"""Application settings.

DATABASE_URL defaults to a local SQLite file so the backend runs without
any external services. Point it at Postgres in production, e.g.:
DATABASE_URL=postgresql://user:password@localhost:5432/finpilot
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_SECRET_KEY = "dev-secret-key-change-in-production"


class Settings(BaseSettings):
    database_url: str = "sqlite:///./backend/finpilot.db"
    secret_key: str = DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    # Comma-separated origins the frontend is served from, e.g.
    # "https://app.finpilot.ai,https://staging.finpilot.ai". "*" (the
    # default) is fine for local development but must be set explicitly
    # in production once frontend and backend are on different origins.
    cors_origins: str = "*"
    rate_limiting_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
