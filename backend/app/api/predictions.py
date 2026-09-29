from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.prediction import SavingsPredictionRequest, SavingsPredictionResponse
from src.pipeline.predict import predict_savings

router = APIRouter(prefix="/predict", tags=["predictions"])


@router.post("/savings", response_model=SavingsPredictionResponse)
def predict_savings_endpoint(
    payload: SavingsPredictionRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        prediction = predict_savings(payload.model_dump())
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction model is not available; run the training pipeline first.",
        ) from exc
    return SavingsPredictionResponse(predicted_desired_savings=prediction)
