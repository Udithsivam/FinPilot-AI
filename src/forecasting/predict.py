"""Inference helpers for the expense-forecast pipeline.

Builds the same monthly-panel features used at training time from a
user's own transaction history, then applies the saved pipeline to
forecast their next calendar month's total expense.
"""

import hashlib
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from src.forecasting.features import FEATURE_COLUMNS, build_monthly_panel, latest_feature_row

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PIPELINE_PATH = PROJECT_ROOT / "models" / "expense_forecast_pipeline.pkl"


@lru_cache(maxsize=4)
def _load_pipeline_cached(path: Path):
    return joblib.load(path)


def load_pipeline(path: Path = DEFAULT_PIPELINE_PATH):
    return _load_pipeline_cached(path)


def clear_pipeline_cache() -> None:
    _load_pipeline_cached.cache_clear()
    get_model_metadata.cache_clear()


@lru_cache(maxsize=4)
def get_model_metadata(path: Path = DEFAULT_PIPELINE_PATH) -> dict:
    pipeline = load_pipeline(path)
    model_type = type(pipeline.named_steps["model"]).__name__
    file_hash = hashlib.md5(Path(path).read_bytes(), usedforsecurity=False).hexdigest()[:8]
    return {"model_type": model_type, "model_version": file_hash}


class InsufficientHistoryError(Exception):
    """Raised when a user doesn't have enough transaction history (at
    least two distinct calendar months of expenses) to forecast from."""


def forecast_next_month_expense(transactions: pd.DataFrame, user_id: int, pipeline=None) -> dict:
    """Forecast next month's total expense for one user.

    `transactions` must have columns: user_id, date, amount,
    transaction_type, category, is_recurring — the same shape as the
    training data (see src/forecasting/features.py).
    """
    monthly = build_monthly_panel(transactions)
    row = latest_feature_row(monthly, user_id)
    if row is None:
        raise InsufficientHistoryError(
            "At least two months of expense transactions are required to forecast next month's expense."
        )

    pipeline = pipeline or load_pipeline()
    features = pd.DataFrame([row[FEATURE_COLUMNS]])
    predicted = float(pipeline.predict(features)[0])
    baseline = float(row["rolling_avg_expense"])
    forecast_period = str(row["month"] + 1)

    return {
        "forecast_period": forecast_period,
        "predicted_expense": predicted,
        "baseline_comparison": baseline,
    }
