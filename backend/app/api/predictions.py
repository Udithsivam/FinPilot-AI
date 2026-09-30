from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.prediction import (
    ActualValueUpdate,
    CashFlowForecastResponse,
    ExpenseForecastResponse,
    PredictionHistoryItem,
    SavingsPredictionRequest,
    SavingsPredictionResponse,
)
from backend.app.services.cashflow_service import (
    InsufficientHistoryError as CashFlowInsufficientHistoryError,
    forecast_cash_flow_for_user,
)
from backend.app.services.forecast_service import InsufficientHistoryError, forecast_expense_for_user
from backend.app.services.prediction_service import list_predictions, record_actual_value, record_prediction
from src.cashflow.predict import get_model_metadata as get_cashflow_model_metadata
from src.forecasting.predict import get_model_metadata as get_forecast_model_metadata
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


@history_router.get("/expenses", response_model=ExpenseForecastResponse)
def expense_forecast(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        forecast = forecast_expense_for_user(db, current_user.id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Expense forecasting model is not available; run its training pipeline first.",
        ) from exc
    except InsufficientHistoryError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    metadata = get_forecast_model_metadata()
    prediction = record_prediction(
        db,
        user_id=current_user.id,
        prediction_type="expense_forecast",
        prediction_value=f"{forecast['predicted_expense']:.2f}",
        model_name=metadata["model_type"],
        model_version=metadata["model_version"],
    )

    return ExpenseForecastResponse(
        prediction_id=prediction.id,
        forecast_period=forecast["forecast_period"],
        predicted_expense=forecast["predicted_expense"],
        baseline_comparison=forecast["baseline_comparison"],
        model_name=metadata["model_type"],
        model_version=metadata["model_version"],
        created_at=prediction.created_at,
    )


@history_router.patch("/{prediction_id}/actual", response_model=PredictionHistoryItem)
def set_actual_value(
    prediction_id: int,
    payload: ActualValueUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record the later-known real outcome for one of the caller's own
    past predictions (e.g. what a month's actual expense turned out to
    be), so prediction-performance monitoring has real ground truth to
    compare against instead of reporting insufficient_data forever."""
    prediction = record_actual_value(db, current_user.id, prediction_id, payload.actual_value)
    if prediction is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return prediction


@history_router.get("/cash-flow", response_model=CashFlowForecastResponse)
def cash_flow_forecast(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        forecast = forecast_cash_flow_for_user(db, current_user.id)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cash-flow forecasting model is not available; run its training pipeline first.",
        ) from exc
    except CashFlowInsufficientHistoryError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    metadata = get_cashflow_model_metadata()
    prediction = record_prediction(
        db,
        user_id=current_user.id,
        prediction_type="cash_flow_forecast",
        prediction_value=f"{forecast['predicted_net_cash_flow']:.2f}",
        model_name=metadata["model_type"],
        model_version=metadata["model_version"],
    )

    return CashFlowForecastResponse(
        prediction_id=prediction.id,
        forecast_period=forecast["forecast_period"],
        predicted_income=forecast["predicted_income"],
        predicted_expense=forecast["predicted_expense"],
        predicted_net_cash_flow=forecast["predicted_net_cash_flow"],
        baseline_comparison=forecast["baseline_comparison"],
        model_name=metadata["model_type"],
        model_version=metadata["model_version"],
        created_at=prediction.created_at,
    )
