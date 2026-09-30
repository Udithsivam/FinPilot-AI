"""Train the next-month expense forecasting model.

data/raw/finpilot_transactions.csv (SYNTHETIC, see
scripts/generate_transaction_data.py) -> monthly panel per user ->
chronological train/val/test split -> baseline (historical moving
average) vs. ML candidates -> select on validation MAE -> evaluate on
test -> MLflow -> save artifact.

Split strategy: CHRONOLOGICAL, not random. This predicts a future value
(next month's expense) from past values (this month's and prior months'
expenses) — a random split would let the model train on rows whose
target month is earlier than other training rows' feature month,
leaking future information backward. Every row's target month here is
strictly later than every train-split row used to pick the model and
strictly later than the val-split row used to select between
candidates.

Usage:
    python -m src.forecasting.train
"""

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline

from src.forecasting.features import FEATURE_COLUMNS, TARGET_COLUMN, build_monthly_panel, build_supervised_frame
from src.pipeline.tracking import current_git_commit

try:
    from xgboost import XGBRegressor

    _XGBOOST_AVAILABLE = True
except ImportError:
    _XGBOOST_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "finpilot_transactions.csv"
PIPELINE_PATH = PROJECT_ROOT / "models" / "expense_forecast_pipeline.pkl"
METRICS_PATH = PROJECT_ROOT / "reports" / "expense_forecast_metrics.json"

EXPERIMENT_NAME = "finpilot-expense-forecasting"
REGISTERED_MODEL_NAME = "finpilot-expense-forecaster"

RANDOM_STATE = 42


def _regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    nonzero = y_true != 0
    mape = float((np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])).mean() * 100) if nonzero.any() else None
    metrics = {"mae": float(mae), "rmse": rmse}
    if mape is not None:
        metrics["mape"] = mape
    return metrics


def load_and_validate() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Generate it first: python -m scripts.generate_transaction_data"
        )
    df = pd.read_csv(DATA_PATH)
    df = df.rename(columns={"recurring": "is_recurring"})
    if (df["amount"] <= 0).any():
        raise ValueError("Data validation failed: non-positive amount values found")
    return df


def chronological_split(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unique_target_months = sorted(frame["target_month"].unique())
    if len(unique_target_months) < 3:
        raise ValueError(
            f"Need at least 3 distinct target months for a train/val/test split, got {len(unique_target_months)}"
        )
    train_months = unique_target_months[:-2]
    val_month = unique_target_months[-2]
    test_month = unique_target_months[-1]

    train_df = frame[frame["target_month"].isin(train_months)]
    val_df = frame[frame["target_month"] == val_month]
    test_df = frame[frame["target_month"] == test_month]
    return train_df, val_df, test_df


def run_training() -> dict:
    df = load_and_validate()
    monthly = build_monthly_panel(df)
    frame = build_supervised_frame(monthly)

    train_df, val_df, test_df = chronological_split(frame)

    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[TARGET_COLUMN]
    X_val, y_val = val_df[FEATURE_COLUMNS], val_df[TARGET_COLUMN]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[TARGET_COLUMN]

    # Baseline: the same historical-moving-average feature already computed
    # per row (2-month rolling mean of past expense), used directly as the
    # forecast with no training at all.
    baseline_val_metrics = _regression_metrics(y_val, val_df["rolling_avg_expense"].to_numpy())
    baseline_test_metrics = _regression_metrics(y_test, test_df["rolling_avg_expense"].to_numpy())

    candidates = {
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=200, max_depth=5, random_state=RANDOM_STATE
        ),
        "GradientBoostingRegressor": GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05, random_state=RANDOM_STATE
        ),
    }
    if _XGBOOST_AVAILABLE:
        candidates["XGBRegressor"] = XGBRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05, random_state=RANDOM_STATE, verbosity=0
        )

    results = {}
    for name, estimator in candidates.items():
        pipeline = Pipeline(steps=[("model", estimator)])
        pipeline.fit(X_train, y_train)
        val_pred = pipeline.predict(X_val)
        results[name] = {
            "pipeline": pipeline,
            "val_metrics": _regression_metrics(y_val, val_pred),
        }

    best_name = min(results, key=lambda name: results[name]["val_metrics"]["mae"])
    best_pipeline = results[best_name]["pipeline"]
    test_pred = best_pipeline.predict(X_test)
    best_test_metrics = _regression_metrics(y_test, test_pred)

    metrics = {
        "dataset": "data/raw/finpilot_transactions.csv (synthetic)",
        "split": "chronological by target month",
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
        "xgboost_available": _XGBOOST_AVAILABLE,
        "selected_model": best_name,
        "baseline": {
            "method": "2-month historical moving average",
            "val": baseline_val_metrics,
            "test": baseline_test_metrics,
        },
        "candidates": {name: r["val_metrics"] for name, r in results.items()},
        "selected_model_test_metrics": best_test_metrics,
        "beats_baseline_on_test_mae": best_test_metrics["mae"] < baseline_test_metrics["mae"],
    }

    PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, PIPELINE_PATH)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    mlflow.set_tracking_uri(f"sqlite:///{(PROJECT_ROOT / 'mlflow.db').as_posix()}")
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name="expense_forecast_training"):
        git_commit = current_git_commit(PROJECT_ROOT)
        if git_commit:
            mlflow.set_tag("git_commit", git_commit)
        mlflow.log_params(
            {
                "n_train": len(X_train),
                "n_val": len(X_val),
                "n_test": len(X_test),
                "n_features": len(FEATURE_COLUMNS),
                "random_state": RANDOM_STATE,
            }
        )
        mlflow.log_metrics({f"baseline_test_{k}": v for k, v in baseline_test_metrics.items()})
        for name, r in results.items():
            with mlflow.start_run(run_name=name, nested=True):
                mlflow.log_param("model_type", name)
                mlflow.log_metrics({f"val_{k}": v for k, v in r["val_metrics"].items()})
        mlflow.set_tag("selected_model", best_name)
        mlflow.log_metrics({f"test_{k}": v for k, v in best_test_metrics.items()})
        mlflow.sklearn.log_model(
            best_pipeline,
            name="model",
            registered_model_name=REGISTERED_MODEL_NAME,
            serialization_format="cloudpickle",
        )

    return metrics


def main() -> None:
    metrics = run_training()
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
