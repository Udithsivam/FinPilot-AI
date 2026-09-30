import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from src.anomaly.detect import detect_anomalies


def anomalies_for_user(db: Session, user_id: int) -> list[dict]:
    rows = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    df = pd.DataFrame(
        [
            {
                "transaction_id": t.id,
                "user_id": user_id,
                "date": t.date,
                "amount": t.amount,
                "transaction_type": t.type,
                "category": t.category,
                "merchant": t.merchant,
                "is_recurring": t.is_recurring,
            }
            for t in rows
        ],
        columns=[
            "transaction_id",
            "user_id",
            "date",
            "amount",
            "transaction_type",
            "category",
            "merchant",
            "is_recurring",
        ],
    )
    if df.empty:
        return []
    return detect_anomalies(df)
