import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class GoalCreate(BaseModel):
    name: str = Field(min_length=1)
    target_amount: float = Field(gt=0)
    current_amount: float = Field(ge=0, default=0.0)
    target_date: dt.date | None = None


class GoalOut(GoalCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class GoalProgress(GoalOut):
    progress_pct: float
