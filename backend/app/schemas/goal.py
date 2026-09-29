import datetime as dt

from pydantic import BaseModel, ConfigDict


class GoalCreate(BaseModel):
    name: str
    target_amount: float
    current_amount: float = 0.0
    target_date: dt.date | None = None


class GoalOut(GoalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GoalProgress(GoalOut):
    progress_pct: float
