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
