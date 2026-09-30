"""Inference helpers for the cash-flow forecast bundle (income_model +
expense_model), mirroring src/forecasting/predict.py."""

import hashlib
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from src.cashflow.features import FEATURE_COLUMNS, build_monthly_panel, latest_feature_row

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PIPELINE_PATH = PROJECT_ROOT / "models" / "cashflow_forecast_pipeline.pkl"


@lru_cache(maxsize=4)
def _load_bundle_cached(path: Path):
    return joblib.load(path)


def load_bundle(path: Path = DEFAULT_PIPELINE_PATH):
    return _load_bundle_cached(path)


def clear_pipeline_cache() -> None:
    _load_bundle_cached.cache_clear()
    get_model_metadata.cache_clear()


@lru_cache(maxsize=4)
def get_model_metadata(path: Path = DEFAULT_PIPELINE_PATH) -> dict:
    bundle = load_bundle(path)
    income_type = type(bundle["income_model"].named_steps["model"]).__name__
    expense_type = type(bundle["expense_model"].named_steps["model"]).__name__
    file_hash = hashlib.md5(Path(path).read_bytes(), usedforsecurity=False).hexdigest()[:8]
    return {"model_type": f"{income_type}+{expense_type}", "model_version": file_hash}


class InsufficientHistoryError(Exception):
    pass


def forecast_next_month_cash_flow(transactions: pd.DataFrame, user_id: int, bundle=None) -> dict:
    monthly = build_monthly_panel(transactions)
    row = latest_feature_row(monthly, user_id)
    if row is None:
        raise InsufficientHistoryError(
            "At least two months of transaction history are required to forecast next month's cash flow."
        )

    bundle = bundle or load_bundle()
    features = pd.DataFrame([row[FEATURE_COLUMNS]])
    predicted_income = float(bundle["income_model"].predict(features)[0])
    predicted_expense = float(bundle["expense_model"].predict(features)[0])

    return {
        "forecast_period": str(row["month"] + 1),
        "predicted_income": predicted_income,
        "predicted_expense": predicted_expense,
        "predicted_net_cash_flow": predicted_income - predicted_expense,
        "baseline_comparison": float(row["rolling_cash_flow"]),
    }
