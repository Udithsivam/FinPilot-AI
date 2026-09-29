from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.database.session import get_db
from backend.app.models.budget import Budget
from backend.app.models.user import User
from backend.app.schemas.budget import BudgetCreate, BudgetOut, BudgetStatus
from backend.app.services.budget_service import budget_status, spent_for_budget

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetOut, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = Budget(user_id=current_user.id, **payload.model_dump())
    db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


@router.get("", response_model=list[BudgetStatus])
def list_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    results = []
    for budget in budgets:
        spent = spent_for_budget(db, current_user.id, budget.category, budget.period)
        results.append(
            BudgetStatus(
                id=budget.id,
                category=budget.category,
                amount=budget.amount,
                period=budget.period,
                **budget_status(spent, budget.amount),
            )
        )
    return results


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == current_user.id).first()
    if budget is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    db.delete(budget)
    db.commit()
