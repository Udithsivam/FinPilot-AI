import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict


class SavingsPredictionRequest(BaseModel):
    Income: float
    Age: int
    Dependents: int
    Occupation: Literal["Student", "Professional", "Self_Employed", "Retired"]
    City_Tier: Literal["Tier_1", "Tier_2", "Tier_3"]
    Rent: float
    Loan_Repayment: float
    Insurance: float
    Groceries: float
    Transport: float
    Eating_Out: float
    Entertainment: float
    Utilities: float
    Healthcare: float
    Education: float
    Miscellaneous: float


class FeatureImpact(BaseModel):
    feature: str
    impact: float
    direction: Literal["positive", "negative"]


class SavingsPredictionResponse(BaseModel):
    predicted_desired_savings: float
    model_type: str
    model_version: str
    explanation: list[FeatureImpact]


class PredictionHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_type: str
    prediction_value: str
    model_name: str
    model_version: str
    created_at: dt.datetime
    actual_value: str | None
    status: str


class CategorizeRequest(BaseModel):
    merchant: str | None = None
    description: str | None = None


class CategorizeResponse(BaseModel):
    prediction_id: int
    category: str
    subcategory: str
    confidence: float
    needs_review: bool
    model_version: str


class ExpenseForecastResponse(BaseModel):
    prediction_id: int
    forecast_period: str
    predicted_expense: float
    baseline_comparison: float
    model_name: str
    model_version: str
    created_at: dt.datetime


class ActualValueUpdate(BaseModel):
    actual_value: str


class CashFlowForecastResponse(BaseModel):
    prediction_id: int
    forecast_period: str
    predicted_income: float
    predicted_expense: float
    predicted_net_cash_flow: float
    baseline_comparison: float
    model_name: str
    model_version: str
    created_at: dt.datetime
