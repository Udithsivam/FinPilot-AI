"""Rule-based, deterministic personalized recommendations.

Every recommendation is generated from the user's own real data (same
principle as insights_service.py and health_score_service.py) — no LLM,
no generic motivational text. Each one states what was detected, why it
matters, and a concrete action, with real numbers substituted in.
"""

import datetime as dt

from sqlalchemy.orm import Session

from backend.app.models.budget import Budget
from backend.app.models.transaction import Transaction
from backend.app.services import analytics_service
from backend.app.services.budget_service import budget_status, spent_for_budget

CATEGORY_INCREASE_THRESHOLD_PCT = 20.0
BUDGET_UTILIZATION_THRESHOLD_PCT = 90.0
SAVINGS_RATE_DROP_THRESHOLD_PCT = 5.0
RECURRING_EXPENSE_SHARE_THRESHOLD_PCT = 50.0


def _category_increase_recommendations(db: Session, user_id: int) -> list[dict]:
    by_month = analytics_service.expense_totals_by_month_and_category(db, user_id)
    months = sorted(by_month.keys())
    if len(months) < 2:
        return []

    current_month, previous_month = months[-1], months[-2]
    current, previous = by_month[current_month], by_month[previous_month]

    recommendations = []
    for category, current_amount in current.items():
        previous_amount = previous.get(category, 0.0)
        if previous_amount <= 0:
            continue
        change_pct = (current_amount - previous_amount) / previous_amount * 100
        if change_pct < CATEGORY_INCREASE_THRESHOLD_PCT:
            continue
        recommendations.append(
            {
                "type": "category_review",
                "title": f"{category} spending increased",
                "evidence": f"{category} spending increased {change_pct:.0f}% compared with last month "
                f"(₹{previous_amount:,.0f} → ₹{current_amount:,.0f}).",
                "reason": "This increase reduces how much you're able to save this month.",
                "action": f"Review your {category} transactions from {current_month} and identify what changed.",
                "priority": "high" if change_pct >= 40 else "medium",
            }
        )
    return recommendations


def _budget_utilization_recommendations(db: Session, user_id: int) -> list[dict]:
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()
    recommendations = []
    for budget in budgets:
        spent = spent_for_budget(db, user_id, budget.category, budget.period)
        status = budget_status(spent, budget.amount)
        if status["utilization_pct"] < BUDGET_UTILIZATION_THRESHOLD_PCT:
            continue
        recommendations.append(
            {
                "type": "budget_adjustment",
                "title": f"{budget.category} budget is nearly used up",
                "evidence": f"You've spent ₹{spent:,.0f} of your ₹{budget.amount:,.0f} {budget.category} "
                f"budget for {budget.period} ({status['utilization_pct']:.0f}%).",
                "reason": "Continuing at this rate will exceed the budget before the period ends.",
                "action": f"Either slow {budget.category} spending for the rest of {budget.period}, or "
                "raise the budget if the higher spending is expected to continue.",
                "priority": "high" if status["status"] == "exceeded" else "medium",
            }
        )
    return recommendations


def _savings_rate_recommendation(db: Session, user_id: int) -> list[dict]:
    months = analytics_service.monthly_breakdown(db, user_id)
    if len(months) < 2:
        return []

    def rate(month: dict) -> float | None:
        return (month["income"] - month["expenses"]) / month["income"] * 100 if month["income"] > 0 else None

    current_rate, previous_rate = rate(months[-1]), rate(months[-2])
    if current_rate is None or previous_rate is None:
        return []
    drop = previous_rate - current_rate
    if drop < SAVINGS_RATE_DROP_THRESHOLD_PCT:
        return []

    return [
        {
            "type": "expense_reduction",
            "title": "Savings rate dropped",
            "evidence": f"Your savings rate fell from {previous_rate:.0f}% to {current_rate:.0f}% "
            f"month over month.",
            "reason": "A falling savings rate slows progress toward your financial goals.",
            "action": "Compare this month's category spending against last month's to find where the drop came from.",
            "priority": "high" if drop >= 15 else "medium",
        }
    ]


def _recurring_expense_recommendation(db: Session, user_id: int) -> list[dict]:
    transactions = (
        db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.type == "expense").all()
    )
    total = sum(t.amount for t in transactions)
    if total <= 0:
        return []
    recurring_total = sum(t.amount for t in transactions if t.is_recurring)
    share = recurring_total / total * 100
    if share < RECURRING_EXPENSE_SHARE_THRESHOLD_PCT:
        return []

    return [
        {
            "type": "recurring_review",
            "title": "Recurring expenses are a large share of spending",
            "evidence": f"Recurring transactions make up {share:.0f}% of your total recorded expenses "
            f"(₹{recurring_total:,.0f} of ₹{total:,.0f}).",
            "reason": "High fixed costs leave less room to absorb unexpected expenses or save more.",
            "action": "Review your recurring subscriptions and commitments for any you no longer need.",
            "priority": "low",
        }
    ]


def generate_recommendations(db: Session, user_id: int) -> list[dict]:
    recommendations = (
        _budget_utilization_recommendations(db, user_id)
        + _savings_rate_recommendation(db, user_id)
        + _category_increase_recommendations(db, user_id)
        + _recurring_expense_recommendation(db, user_id)
    )
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    recommendations.sort(key=lambda r: priority_rank.get(r["priority"], 3))

    now = dt.datetime.now(dt.timezone.utc)
    return [{"id": i + 1, "created_at": now, **rec} for i, rec in enumerate(recommendations[:5])]
