"""FastAPI application entrypoint.

Run with: uvicorn backend.app.main:app --reload
"""

import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

import backend.app.models  # noqa: F401 — registers all models before create_all
from backend.app.api import (
    ai,
    analytics,
    auth,
    budgets,
    feedback,
    goals,
    mlops,
    monitoring,
    predictions,
    transactions,
    users,
)
from backend.app.core.config import DEFAULT_SECRET_KEY, get_settings
from backend.app.database.base import Base
from backend.app.database.session import engine, get_db

logger = logging.getLogger("finpilot")

settings = get_settings()

if settings.secret_key == DEFAULT_SECRET_KEY:
    logger.warning(
        "SECRET_KEY is using its default value. This signs every JWT issued by "
        "this server — set the SECRET_KEY environment variable to a long random "
        "value before deploying anywhere other than local development."
    )

app = FastAPI(title="FinPilot AI", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.cors_origins == "*" else settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

Instrumentator().instrument(app).expose(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(predictions.history_router)
app.include_router(feedback.router)
app.include_router(ai.router)
app.include_router(monitoring.router)
app.include_router(mlops.router)


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unavailable"
    return {"status": "ok", "database": db_status}
