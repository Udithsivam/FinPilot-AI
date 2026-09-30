from typing import Literal

from pydantic import BaseModel


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


class SavingsPredictionResponse(BaseModel):
    predicted_desired_savings: float
    model_type: str
    model_version: str
