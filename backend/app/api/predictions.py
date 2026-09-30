from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.prediction import (
    PredictionHistoryItem,
    SavingsPredictionRequest,
    SavingsPredictionResponse,
)
from backend.app.services.prediction_service import list_predictions, record_prediction
from src.pipeline.explain import explain_prediction
from src.pipeline.predict import get_model_metadata, predict_savings

router = APIRouter(prefix="/predict", tags=["predictions"])
history_router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.post("/savings", response_model=SavingsPredictionResponse)
def predict_savings_endpoint(
    payload: SavingsPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        prediction = predict_savings(payload.model_dump())
        metadata = get_model_metadata()
        explanation = explain_prediction(payload.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model is not available; run the training pipeline first.",
        ) from exc

    record_prediction(
        db,
        user_id=current_user.id,
        prediction_type="savings",
        prediction_value=f"{prediction:.2f}",
        model_name=metadata["model_type"],
        model_version=metadata["model_version"],
    )

    return SavingsPredictionResponse(
        predicted_desired_savings=prediction,
        explanation=explanation,
        **metadata,
    )


@history_router.get("/history", response_model=list[PredictionHistoryItem])
def prediction_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return list_predictions(db, current_user.id)
