from sqlalchemy.orm import Session

from backend.app.models.prediction import Prediction


def record_prediction(
    db: Session, user_id: int, prediction_type: str, prediction_value: str, model_name: str, model_version: str
) -> Prediction:
    prediction = Prediction(
        user_id=user_id,
        prediction_type=prediction_type,
        prediction_value=prediction_value,
        model_name=model_name,
        model_version=model_version,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def list_predictions(db: Session, user_id: int) -> list[Prediction]:
    return (
        db.query(Prediction)
        .filter(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
        .all()
    )


def record_actual_value(db: Session, user_id: int, prediction_id: int, actual_value: str) -> Prediction | None:
    """Attach a later-known real outcome to a past prediction, scoped to
    the owning user. Returns None (never another user's row) if no
    matching prediction exists — this is what makes prediction
    performance monitoring (src/monitoring/performance.py) able to
    compute a real MAE/RMSE/R² instead of reporting insufficient_data
    forever."""
    prediction = (
        db.query(Prediction)
        .filter(Prediction.id == prediction_id, Prediction.user_id == user_id)
        .first()
    )
    if prediction is None:
        return None
    prediction.actual_value = actual_value
    prediction.status = "confirmed"
    db.commit()
    db.refresh(prediction)
    return prediction


def all_predictions_with_actuals(db: Session, prediction_type: str) -> list[Prediction]:
    """Across ALL users — used only by the admin-gated monitoring/MLOps
    endpoints, never exposed to a normal user's own request handlers."""
    return (
        db.query(Prediction)
        .filter(Prediction.prediction_type == prediction_type, Prediction.actual_value.is_not(None))
        .all()
    )
