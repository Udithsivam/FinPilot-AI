"""Admin-only monitoring: prediction performance and feature drift.

Both draw on real data only:
- Performance: Prediction rows (across all users) that have had an
  actual_value recorded via PATCH /predictions/{id}/actual.
- Drift: the synthetic training dataset's transaction amounts (the
  reference distribution the categorizer/forecast models were trained
  on) versus the real authenticated users' actual transaction amounts
  recorded in this deployment (the production/inference distribution).
"""

from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.services.prediction_service import all_predictions_with_actuals
from src.monitoring.drift import detect_feature_drift
from src.monitoring.performance import evaluate_predictions

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TRAINING_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "finpilot_transactions.csv"


def performance_summary(db: Session) -> list[dict]:
    results = []
    for prediction_type in ["savings", "expense_forecast", "cash_flow_forecast", "categorization"]:
        rows: list[Prediction] = all_predictions_with_actuals(db, prediction_type)
        by_model: dict[tuple[str, str], list[tuple[float, float]]] = {}
        for row in rows:
            try:
                predicted = float(row.prediction_value)
                actual = float(row.actual_value)
            except (TypeError, ValueError):
                continue
            key = (row.model_name, row.model_version)
            by_model.setdefault(key, []).append((predicted, actual))

        if not by_model:
            results.append(
                {
                    "prediction_type": prediction_type,
                    "model_name": None,
                    "model_version": None,
                    "sample_count": 0,
                    "status": "insufficient_data",
                    "mae": None,
                    "rmse": None,
                    "r2": None,
                }
            )
            continue

        for (model_name, model_version), pairs in by_model.items():
            results.append(evaluate_predictions(prediction_type, model_name, model_version, pairs))

    return results


def drift_summary(db: Session) -> list[dict]:
    if not TRAINING_DATA_PATH.exists():
        return [
            {
                "feature": "transaction_amount",
                "metric": "kolmogorov_smirnov",
                "value": None,
                "threshold": None,
                "status": "insufficient_data",
                "reference_size": 0,
                "current_size": 0,
            }
        ]

    reference_df = pd.read_csv(TRAINING_DATA_PATH)
    reference_amounts = reference_df[reference_df["transaction_type"] == "expense"]["amount"].tolist()

    current_amounts = [
        t.amount for t in db.query(Transaction).filter(Transaction.type == "expense").all()
    ]

    return [detect_feature_drift("transaction_amount", reference_amounts, current_amounts)]
