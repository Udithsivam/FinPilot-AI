import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction
from src.search.semantic_search import search_transactions


def semantic_search_for_user(db: Session, user_id: int, query: str, top_k: int = 10) -> list[dict]:
    # Filtered by user_id at the query level, before anything is ranked or
    # returned — a user's transactions never enter another user's search
    # corpus.
    rows = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    df = pd.DataFrame(
        [
            {
                "transaction_id": t.id,
                "merchant": t.merchant,
                "description": t.description,
                "category": t.category,
                "amount": t.amount,
                "date": t.date,
            }
            for t in rows
        ],
        columns=["transaction_id", "merchant", "description", "category", "amount", "date"],
    )
    return search_transactions(df, query, top_k=top_k)
