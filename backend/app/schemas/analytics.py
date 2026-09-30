import datetime as dt
from typing import Literal

from pydantic import BaseModel


class CategoryAmount(BaseModel):
    category: str
    amount: float


class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_cash_flow: float
    savings: float
    savings_rate: float
    top_categories: list[CategoryAmount]


class MonthlyBreakdown(BaseModel):
    month: str  # "YYYY-MM"
    income: float
    expenses: float


class Insight(BaseModel):
    title: str
    description: str
    tone: Literal["success", "warning"]


class Recommendation(BaseModel):
    id: int
    type: str
    title: str
    evidence: str
    reason: str
    action: str
    priority: Literal["high", "medium", "low"]
    created_at: dt.datetime
