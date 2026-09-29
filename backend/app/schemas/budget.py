from pydantic import BaseModel, ConfigDict


class BudgetCreate(BaseModel):
    category: str
    amount: float
    period: str  # "YYYY-MM"


class BudgetOut(BudgetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BudgetStatus(BudgetOut):
    spent: float
    remaining: float
    utilization_pct: float
    status: str  # "normal" | "approaching_limit" | "exceeded"
