from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_admin
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.monitoring import DriftMetric, PerformanceMetric
from backend.app.services import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/performance", response_model=list[PerformanceMetric])
def performance(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Admin-only: real MAE/RMSE/R² per model, computed only from
    predictions that have a recorded actual outcome. Never exposed to
    ordinary users — this aggregates across ALL users' predictions."""
    return monitoring_service.performance_summary(db)


@router.get("/drift", response_model=list[DriftMetric])
def drift(current_admin: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Admin-only: Kolmogorov-Smirnov drift check between the training
    dataset's transaction-amount distribution and the real, currently
    recorded transaction amounts across all users."""
    return monitoring_service.drift_summary(db)
