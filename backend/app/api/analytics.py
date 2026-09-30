from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.user import User
from backend.app.schemas.analytics import CategoryAmount, DashboardSummary, Insight, MonthlyBreakdown, Recommendation
from backend.app.schemas.health import HealthScoreResponse
from backend.app.services import analytics_service, health_score_service, insights_service, recommendation_service

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


@router.get("/health-score", response_model=HealthScoreResponse)
def health_score(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return health_score_service.compute_health_score(db, current_user.id)


@router.get("/insights", response_model=list[Insight])
def insights(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return insights_service.generate_insights(db, current_user.id)


@router.get("/recommendations", response_model=list[Recommendation])
def recommendations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return recommendation_service.generate_recommendations(db, current_user.id)
