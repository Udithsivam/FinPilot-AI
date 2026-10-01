from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.transaction import Transaction
from backend.app.models.user import User
from backend.app.schemas.prediction import CategorizeRequest, CategorizeResponse, ReceiptOCRResponse
from backend.app.schemas.transaction import SemanticSearchResult, TransactionCreate, TransactionOut
from backend.app.services.prediction_service import record_prediction
from backend.app.services.search_service import semantic_search_for_user
from src.categorization.predict import categorize_transaction
from src.ocr.receipt_parser import OCRUnavailableError, extract_text, parse_receipt_fields

router = APIRouter(prefix="/transactions", tags=["transactions"])

MAX_RECEIPT_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB — generous for a phone-camera photo, bounds abuse


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


@router.post("/receipt-ocr", response_model=ReceiptOCRResponse)
async def scan_receipt(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Extract merchant/amount/date from a photographed or scanned
    receipt (Tesseract OCR, see src/ocr/receipt_parser.py), then run the
    same categorization model used by /transactions/categorize on the
    extracted text.

    The receipt image itself is never stored — only the extracted
    structured fields and the resulting category prediction (so a later
    correction can still be recorded as feedback via POST /feedback,
    exactly like a manually-typed transaction). Any field OCR couldn't
    confidently extract comes back as null rather than a guess; the
    caller (the transaction form) is expected to let the user review and
    fill in gaps before saving.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be an image")

    image_bytes = await file.read()
    if len(image_bytes) > MAX_RECEIPT_IMAGE_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image too large")

    try:
        text = extract_text(image_bytes)
    except OCRUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    fields = parse_receipt_fields(text)

    category = subcategory = confidence = needs_review = prediction_id = model_version = None
    if fields["merchant"] or fields["raw_text"]:
        try:
            result = categorize_transaction(fields["merchant"], fields["raw_text"][:500])
            prediction = record_prediction(
                db,
                user_id=current_user.id,
                prediction_type="categorization",
                prediction_value=f"{result['category']} > {result['subcategory']}",
                model_name="TransactionCategorizer",
                model_version=result["model_version"],
            )
            category = result["category"]
            subcategory = result["subcategory"]
            confidence = result["confidence"]
            needs_review = result["needs_review"]
            prediction_id = prediction.id
            model_version = result["model_version"]
        except FileNotFoundError:
            pass  # categorizer artifact missing — OCR fields are still useful on their own

    return ReceiptOCRResponse(
        merchant=fields["merchant"],
        amount=fields["amount"],
        date=fields["date"],
        raw_text=fields["raw_text"],
        category=category,
        subcategory=subcategory,
        confidence=confidence,
        needs_review=needs_review,
        prediction_id=prediction_id,
        model_version=model_version,
    )


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
