from typing import Literal

from pydantic import BaseModel


class PerformanceMetric(BaseModel):
    prediction_type: str
    model_name: str | None
    model_version: str | None
    sample_count: int
    status: Literal["healthy", "insufficient_data"]
    mae: float | None
    rmse: float | None
    r2: float | None


class DriftMetric(BaseModel):
    feature: str
    metric: str
    value: float | None
    threshold: float | None
    status: Literal["stable", "warning", "drift_detected", "insufficient_data"]
    reference_size: int
    current_size: int
