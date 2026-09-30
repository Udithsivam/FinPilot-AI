from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.transaction import Transaction
from backend.app.models.user import User
from backend.app.schemas.prediction import CategorizeRequest, CategorizeResponse
from backend.app.schemas.transaction import SemanticSearchResult, TransactionCreate, TransactionOut
from backend.app.services.prediction_service import record_prediction
from backend.app.services.search_service import semantic_search_for_user
from src.categorization.predict import categorize_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/categorize", response_model=CategorizeResponse)
def categorize_transaction_endpoint(
    payload: CategorizeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Suggest a category/subcategory from merchant + description text.

    Purely a suggestion: the caller (the transaction-creation form) is
    free to use, edit, or ignore it before actually creating the
    transaction. If the user's final choice differs from this
    suggestion, the frontend records that as feedback via POST /feedback
    referencing the returned prediction_id.
    """
    try:
        result = categorize_transaction(payload.merchant, payload.description)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Categorization model is not available; run its training pipeline first.",
        ) from exc

    prediction = record_prediction(
        db,
        user_id=current_user.id,
        prediction_type="categorization",
        prediction_value=f"{result['category']} > {result['subcategory']}",
        model_name="TransactionCategorizer",
        model_version=result["model_version"],
    )

    return CategorizeResponse(prediction_id=prediction.id, **result)


@router.get("/search", response_model=list[SemanticSearchResult])
def search_transactions_endpoint(
    q: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Semantic search over the authenticated user's own transactions
    (TF-IDF + cosine similarity — see src/search/semantic_search.py).
    Always scoped to current_user.id; never returns another user's
    transactions."""
    return semantic_search_for_user(db, current_user.id, q)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = Transaction(user_id=current_user.id, **payload.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
        .order_by(Transaction.date.desc())
        .all()
    )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
        .first()
    )
    if transaction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    db.delete(transaction)
    db.commit()
