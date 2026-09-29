from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.analytics import CategoryAmount, DashboardSummary, MonthlyBreakdown
from backend.app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analytics_service.dashboard_summary(db, current_user.id)


@router.get("/monthly", response_model=list[MonthlyBreakdown])
def monthly(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analytics_service.monthly_breakdown(db, current_user.id)


@router.get("/categories", response_model=list[CategoryAmount])
def categories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return analytics_service.category_breakdown(db, current_user.id)
