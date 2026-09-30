from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.feedback import Feedback
from backend.app.models.prediction import Prediction
from backend.app.models.user import User
from backend.app.schemas.feedback import FeedbackCreate, FeedbackOut

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED)
def create_feedback(
    payload: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a user's correction of a model output (e.g. overriding a
    suggested transaction category). Stored for later review — not
    automatically fed into retraining."""
    if payload.prediction_id is not None:
        owned = (
            db.query(Prediction)
            .filter(Prediction.id == payload.prediction_id, Prediction.user_id == current_user.id)
            .first()
        )
        if owned is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")

    feedback = Feedback(user_id=current_user.id, **payload.model_dump())
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
