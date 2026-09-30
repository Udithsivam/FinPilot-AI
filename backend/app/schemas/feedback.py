import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict


class FeedbackCreate(BaseModel):
    prediction_id: int | None = None
    feedback_type: Literal["category_correction", "prediction_correction", "recommendation_feedback"]
    corrected_value: str | None = None


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_id: int | None
    feedback_type: str
    corrected_value: str | None
    created_at: dt.datetime
