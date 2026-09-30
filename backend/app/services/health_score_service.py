"""Financial Health Score: a rule-based, explainable score.

Deliberately not a black-box model: each factor is a simple, documented
formula over the user's own transactions/budgets/goals, so the score can
always be explained by its inputs. A factor whose underlying data doesn't
exist yet (no budgets, less than two months of expenses, ...) is marked
"Not Enough Data" and excluded from the overall average rather than
guessed, so the score is only ever built from real evidence.
"""

import re
import statistics
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.models.budget import Budget
from backend.app.models.goal import FinancialGoal
from backend.app.models.transaction import Transaction
from backend.app.services import analytics_service
from backend.app.services.budget_service import budget_status, spent_for_budget

DEBT_CATEGORY_PATTERN = re.compile(r"loan|debt|emi", re.IGNORECASE)
EMERGENCY_GOAL_PATTERN = re.compile(r"emergency", re.IGNORECASE)

NOT_ENOUGH_DATA = "Not Enough Data"


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


@dataclass
class Factor:
    key: str
    label: str
    rating: str
    score: float | None
    detail: str


def _savings_rate_factor(summary: dict) -> Factor:
    income = summary["total_income"]
    if income <= 0:
        return Factor("savings_rate", "Savings Rate", NOT_ENOUGH_DATA, None, "No income recorded yet.")
    rate = summary["savings_rate"]
    score = _clamp(rate / 30 * 100)
    rating = "Good" if rate >= 20 else "Moderate" if rate >= 5 else "Low"
    return Factor("savings_rate", "Savings Rate", rating, score, f"Saving {rate:.1f}% of income.")


def _budget_adherence_factor(db: Session, user_id: int) -> Factor:
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    if not budgets:
        return Factor("budget_adherence", "Budget Adherence", NOT_ENOUGH_DATA, None, "No budgets set.")

    not_exceeded = sum(
        1
        for b in budgets
        if budget_status(spent_for_budget(db, user_id, b.category, b.period), b.amount)["status"]
        != "exceeded"
    )
    pct = not_exceeded / len(budgets) * 100
    rating = "Good" if pct >= 80 else "Moderate" if pct >= 50 else "Low"
    return Factor(
        "budget_adherence",
        "Budget Adherence",
        rating,
        pct,
        f"{not_exceeded}/{len(budgets)} budgets within limit.",
    )


def _debt_burden_factor(db: Session, user_id: int, summary: dict) -> Factor:
    income = summary["total_income"]
    if income <= 0:
        return Factor("debt_burden", "Debt Burden", NOT_ENOUGH_DATA, None, "No income recorded yet.")

    transactions = (
        db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.type == "expense").all()
    )
    debt_total = sum(t.amount for t in transactions if DEBT_CATEGORY_PATTERN.search(t.category))
    ratio_pct = debt_total / income * 100
    score = _clamp(100 - ratio_pct * 2.5)
    rating = "Good" if ratio_pct < 10 else "Moderate" if ratio_pct < 25 else "High"
    return Factor(
        "debt_burden", "Debt Burden", rating, score, f"Debt repayments are {ratio_pct:.1f}% of income."
    )


def _expense_stability_factor(db: Session, user_id: int) -> Factor:
    months = analytics_service.monthly_breakdown(db, user_id)
    expense_values = [m["expenses"] for m in months if m["expenses"] > 0]
    if len(expense_values) < 2:
        return Factor(
            "expense_stability",
            "Expense Stability",
            NOT_ENOUGH_DATA,
            None,
            "Need at least two months of expenses.",
        )
    mean = statistics.mean(expense_values)
    stdev = statistics.pstdev(expense_values)
    cv = stdev / mean if mean > 0 else 0.0
    score = _clamp(100 - cv * 200)
    rating = "Good" if cv < 0.15 else "Moderate" if cv < 0.3 else "Low"
    return Factor(
        "expense_stability",
        "Expense Stability",
        rating,
        score,
        f"Month-to-month expense variation is {cv * 100:.0f}%.",
    )


def _emergency_reserve_factor(db: Session, user_id: int) -> Factor:
    goals = db.query(FinancialGoal).filter(FinancialGoal.user_id == user_id).all()
    emergency_goal = next((g for g in goals if EMERGENCY_GOAL_PATTERN.search(g.name)), None)
    months = analytics_service.monthly_breakdown(db, user_id)
    avg_monthly_expenses = statistics.mean([m["expenses"] for m in months]) if months else 0.0

    if emergency_goal is None or avg_monthly_expenses <= 0:
        return Factor(
            "emergency_reserve",
            "Emergency Reserve",
            NOT_ENOUGH_DATA,
            None,
            "No emergency fund goal or expense history yet.",
        )

    months_covered = emergency_goal.current_amount / avg_monthly_expenses
    score = _clamp(months_covered / 6 * 100)
    rating = "Good" if months_covered >= 6 else "Moderate" if months_covered >= 3 else "Low"
    return Factor(
        "emergency_reserve",
        "Emergency Reserve",
        rating,
        score,
        f"Emergency fund covers {months_covered:.1f} months of expenses.",
    )


def compute_health_score(db: Session, user_id: int) -> dict:
    summary = analytics_service.dashboard_summary(db, user_id)
    factors = [
        _savings_rate_factor(summary),
        _budget_adherence_factor(db, user_id),
        _debt_burden_factor(db, user_id, summary),
        _expense_stability_factor(db, user_id),
        _emergency_reserve_factor(db, user_id),
    ]

    scored = [f for f in factors if f.score is not None]
    overall = round(sum(f.score for f in scored) / len(scored), 1) if scored else None

    return {
        "score": overall,
        "factors": [
            {"key": f.key, "label": f.label, "rating": f.rating, "score": f.score, "detail": f.detail}
            for f in factors
        ],
    }
