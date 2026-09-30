from sqlalchemy.orm import Session

from backend.app.models.transaction import Transaction


def dashboard_summary(db: Session, user_id: int) -> dict:
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expenses = sum(t.amount for t in transactions if t.type == "expense")
    net_cash_flow = total_income - total_expenses
    savings_rate = (net_cash_flow / total_income * 100) if total_income > 0 else 0.0

    category_totals: dict[str, float] = {}
    for t in transactions:
        if t.type == "expense":
            category_totals[t.category] = category_totals.get(t.category, 0.0) + t.amount
    top_categories = sorted(
        ({"category": c, "amount": a} for c, a in category_totals.items()),
        key=lambda x: x["amount"],
        reverse=True,
    )[:5]

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": net_cash_flow,
        "savings": net_cash_flow,
        "savings_rate": savings_rate,
        "top_categories": top_categories,
    }


def monthly_breakdown(db: Session, user_id: int) -> list[dict]:
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    months: dict[str, dict[str, float]] = {}
    for t in transactions:
        key = t.date.strftime("%Y-%m")
        bucket = months.setdefault(key, {"income": 0.0, "expenses": 0.0})
        if t.type == "income":
            bucket["income"] += t.amount
        else:
            bucket["expenses"] += t.amount
    return [
        {"month": month, "income": v["income"], "expenses": v["expenses"]}
        for month, v in sorted(months.items())
    ]


def expense_totals_by_month_and_category(db: Session, user_id: int) -> dict[str, dict[str, float]]:
    """{"YYYY-MM": {category: total_amount}} for the user's expense
    transactions — shared by insights_service and recommendation_service
    so month-over-month category comparisons aren't computed twice."""
    transactions = (
        db.query(Transaction).filter(Transaction.user_id == user_id, Transaction.type == "expense").all()
    )
    by_month: dict[str, dict[str, float]] = {}
    for t in transactions:
        month_key = t.date.strftime("%Y-%m")
        bucket = by_month.setdefault(month_key, {})
        bucket[t.category] = bucket.get(t.category, 0.0) + t.amount
    return by_month


def category_breakdown(db: Session, user_id: int) -> list[dict]:
    transactions = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id, Transaction.type == "expense")
        .all()
    )
    totals: dict[str, float] = {}
    for t in transactions:
        totals[t.category] = totals.get(t.category, 0.0) + t.amount
    return sorted(
        ({"category": c, "amount": a} for c, a in totals.items()),
        key=lambda x: x["amount"],
        reverse=True,
    )
