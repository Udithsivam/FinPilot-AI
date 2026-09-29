"""Inference helpers built on the saved production pipeline.

Applies the same feature engineering used at training time before calling
the fitted pipeline, so callers only need to supply raw record fields.
"""

from pathlib import Path

import joblib
import pandas as pd

from src.features.build_features import add_engineered_features

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PIPELINE_PATH = PROJECT_ROOT / "models" / "savings_prediction_pipeline.pkl"


def load_pipeline(path: Path = DEFAULT_PIPELINE_PATH):
    return joblib.load(path)


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
