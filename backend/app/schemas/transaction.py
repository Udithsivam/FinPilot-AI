import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TransactionCreate(BaseModel):
    date: dt.date
    amount: float = Field(gt=0)
    type: Literal["income", "expense"]
    category: str = Field(min_length=1)
    subcategory: str | None = None
    merchant: str | None = None
    payment_method: str | None = None
    description: str | None = None
    is_recurring: bool = False


class TransactionOut(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int


class SemanticSearchResult(BaseModel):
    transaction_id: int
    merchant: str | None
    description: str | None
    category: str
    amount: float
    date: str
    similarity: float
