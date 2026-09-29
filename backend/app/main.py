"""FastAPI application entrypoint.

Run with: uvicorn backend.app.main:app --reload
"""

from fastapi import Depends, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.orm import Session

import backend.app.models  # noqa: F401 — registers all models before create_all
from backend.app.api import analytics, auth, budgets, goals, predictions, transactions, users
from backend.app.database.base import Base
from backend.app.database.session import engine, get_db

app = FastAPI(title="FinPilot AI", version="0.1.0")

Base.metadata.create_all(bind=engine)

Instrumentator().instrument(app).expose(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(goals.router)
app.include_router(analytics.router)
app.include_router(predictions.router)


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "unavailable"
    return {"status": "ok", "database": db_status}
