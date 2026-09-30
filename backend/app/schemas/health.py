from pydantic import BaseModel


class HealthScoreFactor(BaseModel):
    key: str
    label: str
    rating: str  # "Good" | "Moderate" | "Low" | "High" | "Not Enough Data"
    score: float | None  # 0-100, None when rating is "Not Enough Data"
    detail: str


class HealthScoreResponse(BaseModel):
    score: float | None  # 0-100 weighted average of scored factors; None if none could be scored
    factors: list[HealthScoreFactor]
