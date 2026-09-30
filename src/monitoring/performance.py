"""Prediction performance monitoring.

Computes real regression metrics (MAE, RMSE, R²) between a model's past
predictions and their later-recorded actual outcomes. This can only ever
report on predictions that (a) exist and (b) have had an actual outcome
recorded against them — see Prediction.actual_value, set via
PATCH /predictions/{id}/actual (backend/app/api/predictions.py). There is
no mechanism to infer an "actual" outcome automatically (e.g. next
month's real expense isn't known until that month closes and the user's
real transactions are entered), so this module reports "insufficient_data"
honestly rather than fabricating a score from predictions with no
recorded ground truth.
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MIN_SAMPLES = 3


def evaluate_predictions(prediction_type: str, model_name: str, model_version: str, pairs: list[tuple[float, float]]) -> dict:
    """`pairs` is a list of (predicted, actual) for one model/version/type.
    Never fabricates a metric from fewer than MIN_SAMPLES pairs."""
    base = {
        "prediction_type": prediction_type,
        "model_name": model_name,
        "model_version": model_version,
        "sample_count": len(pairs),
    }

    if len(pairs) < MIN_SAMPLES:
        return {**base, "status": "insufficient_data", "mae": None, "rmse": None, "r2": None}

    predicted = np.array([p for p, _ in pairs])
    actual = np.array([a for _, a in pairs])

    mae = float(mean_absolute_error(actual, predicted))
    rmse = float(np.sqrt(mean_squared_error(actual, predicted)))
    # R² is undefined (and misleading) with fewer than 2 distinct actual
    # values — report it as unavailable rather than a meaningless number.
    r2 = float(r2_score(actual, predicted)) if len(set(actual.tolist())) > 1 else None

    return {**base, "status": "healthy", "mae": mae, "rmse": rmse, "r2": r2}
