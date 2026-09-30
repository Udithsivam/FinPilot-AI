import datetime as dt

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction

APPROACHING_LIMIT_THRESHOLD = 0.9


def period_bounds(period: str) -> tuple[dt.date, dt.date]:
    """Return [start, end) dates for a "YYYY-MM" period, without relying on
    database-specific date functions (keeps this portable across SQLite
    and Postgres)."""
    year, month = (int(part) for part in period.split("-"))
    start = dt.date(year, month, 1)
    end = dt.date(year + 1, 1, 1) if month == 12 else dt.date(year, month + 1, 1)
    return start, end


def spent_for_budget(db: Session, user_id: int, category: str, period: str) -> float:
    """Sum expense transactions for a category within a "YYYY-MM" period.

    Category matching is case- and whitespace-insensitive at the database
    level (LOWER + TRIM, both standard SQL supported by SQLite and
    Postgres) so a budget for "Groceries" matches a transaction logged as
    "groceries" or " Groceries ". This only affects this comparison —
    stored category text (as shown elsewhere, e.g. transaction lists and
    category breakdowns) is untouched, and no canonical category taxonomy
    is introduced here.
    """
    start, end = period_bounds(period)
    total = (
        db.query(func.coalesce(func.sum(Transaction.amount), 0.0))
        .filter(
            Transaction.user_id == user_id,
            Transaction.type == "expense",
            func.lower(func.trim(Transaction.category)) == category.strip().lower(),
            Transaction.date >= start,
            Transaction.date < end,
        )
        .scalar()
    )
    return float(total)


def budget_status(spent: float, amount: float) -> dict:
    remaining = amount - spent
    utilization_pct = (spent / amount * 100) if amount > 0 else 0.0

    if spent > amount:
        status = "exceeded"
    elif amount > 0 and spent / amount >= APPROACHING_LIMIT_THRESHOLD:
        status = "approaching_limit"
    else:
        status = "normal"

    return {"spent": spent, "remaining": remaining, "utilization_pct": utilization_pct, "status": status}
