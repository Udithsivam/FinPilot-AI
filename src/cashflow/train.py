"""Train the next-month cash-flow forecasting models.

Trains two regressors — next-month income and next-month expense — from
the same monthly panel, then derives net_cash_flow = income - expense at
inference time. This keeps the three reported numbers internally
consistent (predicted_income - predicted_expense always equals
predicted_net_cash_flow), rather than training a third, independent
net_cash_flow regressor that could disagree with the other two.

Split strategy: CHRONOLOGICAL by target month — same reasoning as
src/forecasting/train.py (forecasting a future value from past values).

Candidates: historical moving-average baseline, RandomForestRegressor,
GradientBoostingRegressor, and XGBoost if installed. Selection is by
validation MAE only, never by which algorithm "sounds" more advanced.

Usage:
    python -m src.cashflow.train
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

from src.cashflow.features import FEATURE_COLUMNS, build_monthly_panel, build_supervised_frame
from src.pipeline.tracking import current_git_commit

try:
    from xgboost import XGBRegressor

    _XGBOOST_AVAILABLE = True
except ImportError:
    _XGBOOST_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "finpilot_transactions.csv"
PIPELINE_PATH = PROJECT_ROOT / "models" / "cashflow_forecast_pipeline.pkl"
METRICS_PATH = PROJECT_ROOT / "reports" / "cashflow_forecast_metrics.json"

EXPERIMENT_NAME = "finpilot-cashflow-forecasting"
REGISTERED_MODEL_NAME = "finpilot-cashflow-forecaster"

RANDOM_STATE = 42


def _regression_metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    nonzero = y_true != 0
    mape = (
        float((np.abs((y_true[nonzero] - y_pred[nonzero]) / y_true[nonzero])).mean() * 100)
        if nonzero.any()
        else None
    )
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
    return (
        frame[frame["target_month"].isin(train_months)],
        frame[frame["target_month"] == val_month],
        frame[frame["target_month"] == test_month],
    )


def _candidates() -> dict:
    candidates = {
        "RandomForestRegressor": RandomForestRegressor(n_estimators=200, max_depth=5, random_state=RANDOM_STATE),
        "GradientBoostingRegressor": GradientBoostingRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05, random_state=RANDOM_STATE
        ),
    }
    if _XGBOOST_AVAILABLE:
        candidates["XGBRegressor"] = XGBRegressor(
            n_estimators=200, max_depth=3, learning_rate=0.05, random_state=RANDOM_STATE, verbosity=0
        )
    return candidates


def _train_target(
    target_col: str,
    baseline_col: str,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> dict:
    X_train, y_train = train_df[FEATURE_COLUMNS], train_df[target_col]
    X_val, y_val = val_df[FEATURE_COLUMNS], val_df[target_col]
    X_test, y_test = test_df[FEATURE_COLUMNS], test_df[target_col]

    baseline_val = _regression_metrics(y_val, val_df[baseline_col].to_numpy())
    baseline_test = _regression_metrics(y_test, test_df[baseline_col].to_numpy())

    results = {}
    for name, estimator in _candidates().items():
        pipeline = Pipeline(steps=[("model", estimator)])
        pipeline.fit(X_train, y_train)
        results[name] = {
            "pipeline": pipeline,
            "val_metrics": _regression_metrics(y_val, pipeline.predict(X_val)),
        }

    best_name = min(results, key=lambda n: results[n]["val_metrics"]["mae"])
    best_pipeline = results[best_name]["pipeline"]
    test_metrics = _regression_metrics(y_test, best_pipeline.predict(X_test))

    return {
        "pipeline": best_pipeline,
        "selected_model": best_name,
        "baseline": {"method": f"2-month historical moving average ({baseline_col})", "val": baseline_val, "test": baseline_test},
        "candidates": {name: r["val_metrics"] for name, r in results.items()},
        "test_metrics": test_metrics,
        "beats_baseline_on_test_mae": test_metrics["mae"] < baseline_test["mae"],
        "n_train": len(X_train),
        "n_val": len(X_val),
        "n_test": len(X_test),
    }


def run_training() -> dict:
    df = load_and_validate()
    monthly = build_monthly_panel(df)
    frame = build_supervised_frame(monthly)
    train_df, val_df, test_df = chronological_split(frame)

    income_result = _train_target("next_month_income", "rolling_income", train_df, val_df, test_df)
    expense_result = _train_target("next_month_expense", "rolling_expense", train_df, val_df, test_df)

    bundle = {"income_model": income_result["pipeline"], "expense_model": expense_result["pipeline"]}

    metrics = {
        "dataset": "data/raw/finpilot_transactions.csv (synthetic)",
        "split": "chronological by target month",
        "xgboost_available": _XGBOOST_AVAILABLE,
        "income": {k: v for k, v in income_result.items() if k != "pipeline"},
        "expense": {k: v for k, v in expense_result.items() if k != "pipeline"},
    }

    PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, PIPELINE_PATH)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    mlflow.set_tracking_uri(f"sqlite:///{(PROJECT_ROOT / 'mlflow.db').as_posix()}")
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name="cashflow_forecast_training"):
        git_commit = current_git_commit(PROJECT_ROOT)
        if git_commit:
            mlflow.set_tag("git_commit", git_commit)
        mlflow.log_params(
            {
                "n_train": income_result["n_train"],
                "n_val": income_result["n_val"],
                "n_test": income_result["n_test"],
                "n_features": len(FEATURE_COLUMNS),
                "xgboost_available": _XGBOOST_AVAILABLE,
            }
        )
        mlflow.set_tag("selected_income_model", income_result["selected_model"])
        mlflow.set_tag("selected_expense_model", expense_result["selected_model"])
        mlflow.log_metrics({f"income_test_{k}": v for k, v in income_result["test_metrics"].items()})
        mlflow.log_metrics({f"expense_test_{k}": v for k, v in expense_result["test_metrics"].items()})
        mlflow.sklearn.log_model(
            bundle["income_model"], name="income_model", registered_model_name=None, serialization_format="cloudpickle"
        )
        mlflow.sklearn.log_model(
            bundle["expense_model"], name="expense_model", registered_model_name=None, serialization_format="cloudpickle"
        )
        # Register the income model as the representative version for this
        # experiment's registered model — both artifacts ship together in
        # the single joblib bundle used at inference time.
        mlflow.sklearn.log_model(
            bundle["income_model"],
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
