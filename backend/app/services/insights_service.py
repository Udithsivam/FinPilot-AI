"""Rule-based, data-driven financial insights.

Deliberately not an ML/LLM feature: every insight here is a plain
comparison over the user's own transactions (month-over-month category
change, a savings-rate streak), in the same spirit as the Financial
Health Score. If there isn't enough transaction history to compute a
comparison, no insight is fabricated for it — an empty list is a valid,
honest result.
"""

from sqlalchemy.orm import Session

from backend.app.services import analytics_service

CATEGORY_CHANGE_THRESHOLD_PCT = 15.0
SAVINGS_STREAK_RATE_PCT = 20.0


def _category_change_insights(db: Session, user_id: int) -> list[dict]:
    by_month = analytics_service.expense_totals_by_month_and_category(db, user_id)
    months = sorted(by_month.keys())
    if len(months) < 2:
        return []

    current_month, previous_month = months[-1], months[-2]
    current, previous = by_month[current_month], by_month[previous_month]

    insights = []
    for category, current_amount in current.items():
        previous_amount = previous.get(category, 0.0)
        if previous_amount <= 0:
            continue
        change_pct = (current_amount - previous_amount) / previous_amount * 100
        if abs(change_pct) < CATEGORY_CHANGE_THRESHOLD_PCT:
            continue
        direction = "increased" if change_pct > 0 else "decreased"
        insights.append(
            {
                "title": f"{category} spending {direction} {abs(change_pct):.0f}%",
                "description": (
                    f"You spent {abs(change_pct):.0f}% {'more' if change_pct > 0 else 'less'} on "
                    f"{category} in {current_month} than in {previous_month}."
                ),
                "tone": "warning" if change_pct > 0 else "success",
            }
        )
    insights.sort(key=lambda i: i["title"])
    return insights


def _savings_streak_insight(db: Session, user_id: int) -> list[dict]:
    months = analytics_service.monthly_breakdown(db, user_id)
    if len(months) < 2:
        return []

    streak = 0
    for month in reversed(months):
        if month["income"] <= 0:
            break
        rate = (month["income"] - month["expenses"]) / month["income"] * 100
        if rate < SAVINGS_STREAK_RATE_PCT:
            break
        streak += 1

    if streak < 2:
        return []

    return [
        {
            "title": "Consistent savings streak",
            "description": f"You've saved at least {SAVINGS_STREAK_RATE_PCT:.0f}% of income for {streak} months running.",
            "tone": "success",
        }
    ]


def generate_insights(db: Session, user_id: int) -> list[dict]:
    insights = _savings_streak_insight(db, user_id) + _category_change_insights(db, user_id)
    return insights[:5]
