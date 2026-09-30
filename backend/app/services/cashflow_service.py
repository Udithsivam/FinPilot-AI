import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from src.cashflow.predict import InsufficientHistoryError, forecast_next_month_cash_flow

__all__ = ["InsufficientHistoryError", "forecast_cash_flow_for_user"]


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


def forecast_cash_flow_for_user(db: Session, user_id: int) -> dict:
    transactions = _transactions_frame(db, user_id)
    return forecast_next_month_cash_flow(transactions, user_id=user_id)
