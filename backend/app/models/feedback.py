import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database.base import Base


class Feedback(Base):
    """A user's correction of a model's output (e.g. overriding a
    suggested transaction category). Stored so it can later be reviewed
    before being used as retraining data — this project does not
    automatically retrain from unvalidated user input."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    prediction_id: Mapped[int | None] = mapped_column(ForeignKey("predictions.id"), nullable=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "category_correction" | ...
    corrected_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=lambda: dt.datetime.now(dt.timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="feedback_entries")
