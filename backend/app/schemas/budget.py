from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category: str = Field(min_length=1)
    amount: float = Field(gt=0)
    period: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")  # "YYYY-MM"


class BudgetOut(BudgetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BudgetStatus(BudgetOut):
    spent: float
    remaining: float
    utilization_pct: float
    status: str  # "normal" | "approaching_limit" | "exceeded"
