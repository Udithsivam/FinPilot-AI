"""Inference helpers built on the saved production pipeline.

Applies the same feature engineering used at training time before calling
the fitted pipeline, so callers only need to supply raw record fields.
"""

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd

from src.features.build_features import add_engineered_features

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PIPELINE_PATH = PROJECT_ROOT / "models" / "savings_prediction_pipeline.pkl"


@lru_cache(maxsize=4)
def _load_pipeline_cached(path: Path):
    return joblib.load(path)


def load_pipeline(path: Path = DEFAULT_PIPELINE_PATH):
    """Load the trained pipeline, cached per path.

    Without caching, every single prediction request re-reads and
    re-deserializes the pipeline file from disk — real, measurable
    latency under any load, and a small window where a concurrent
    retrain-and-overwrite could be read mid-write. Call
    `clear_pipeline_cache()` after deploying a newly trained model so
    the running process picks it up.
    """
    return _load_pipeline_cached(path)


def clear_pipeline_cache() -> None:
    _load_pipeline_cached.cache_clear()


def predict_savings(record: dict, pipeline=None) -> float:
    """Predict Desired_Savings for a single raw financial record.

    `record` must contain the same raw fields used in training (Income,
    Age, Dependents, Occupation, City_Tier, Rent, ...), before feature
    engineering — this function derives the engineered features itself.
    """
    pipeline = pipeline or load_pipeline()
    df = pd.DataFrame([record])
    featured_df = add_engineered_features(df)
    return float(pipeline.predict(featured_df)[0])
