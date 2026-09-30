import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Prediction(Base):
    """One row per ML inference call (savings prediction or transaction
    categorization), so every prediction has a history, a model version
    attached, and a place to later record the actual outcome."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    prediction_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "savings" | "categorization"
    prediction_value: Mapped[str] = mapped_column(String(255), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    actual_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="predicted")  # predicted | confirmed | corrected

    user: Mapped["User"] = relationship(back_populates="predictions")
