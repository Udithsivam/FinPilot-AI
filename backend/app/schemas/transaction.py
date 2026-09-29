import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict


class TransactionCreate(BaseModel):
    date: dt.date
    amount: float
    type: Literal["income", "expense"]
    category: str
    subcategory: str | None = None
    merchant: str | None = None
    payment_method: str | None = None
    description: str | None = None
    is_recurring: bool = False


class TransactionOut(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
