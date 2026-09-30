import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from src.forecasting.predict import InsufficientHistoryError, forecast_next_month_expense

__all__ = ["InsufficientHistoryError", "forecast_expense_for_user"]


def _transactions_frame(db: Session, user_id: int) -> pd.DataFrame:
    rows = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    return pd.DataFrame(
        [
            {
                "user_id": user_id,
                "date": t.date,
                "amount": t.amount,
                "transaction_type": t.type,
                "category": t.category,
                "is_recurring": t.is_recurring,
            }
            for t in rows
        ],
        columns=["user_id", "date", "amount", "transaction_type", "category", "is_recurring"],
    )


def forecast_expense_for_user(db: Session, user_id: int) -> dict:
    """Forecast the given user's next-month total expense from their own
    real transaction history, using the model trained on the synthetic
    dataset. Raises InsufficientHistoryError if they have under two months
    of expense transactions."""
    transactions = _transactions_frame(db, user_id)
    return forecast_next_month_expense(transactions, user_id=user_id)
