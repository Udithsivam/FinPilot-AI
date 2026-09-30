"""Real explainability for the savings-prediction model.

Deliberately NOT SHAP: `shap` isn't installed, and adding it as a new
dependency for one feature isn't justified when this model already
exposes real, honest global feature importances (`feature_importances_`
on the fitted GradientBoostingRegressor — a genuine property of the
trained model, not invented).

Methodology (stated here so the API response never has to pretend to be
something it isn't):
1. Take the model's real global `feature_importances_` (how much each
   feature contributes to the model overall, across all training data)
   and aggregate one-hot-encoded categorical columns back to their
   original feature name.
2. For direction: compare this specific input's value for a feature
   against the TRAINING data's mean for that feature (computed once,
   cached), and combine with that feature's real correlation sign with
   the target in the training data. If the value is above the mean and
   the feature correlates positively with the target (or below mean +
   negative correlation), the direction is "positive"; otherwise
   "negative".

This is coarser than true per-instance attribution (SHAP/LIME) would
be — it's a global importance ranking plus a local directional signal,
not a per-instance decomposition of this exact prediction. That's a
real limitation, not hidden anywhere this is surfaced.
"""

from functools import lru_cache

import pandas as pd

from src.data.load_data import load_raw_data
from src.data.validate_data import validate_data
from src.features.build_features import add_engineered_features
from src.pipeline.predict import load_pipeline
from src.pipeline.train import PROJECT_ROOT, load_params

TOP_K = 5


@lru_cache(maxsize=1)
def _training_reference() -> tuple[dict, dict]:
    """Real per-feature means and target-correlation signs, computed once
    from the actual training data (not invented)."""
    params = load_params()
    data_cfg = params["data"]
    raw_df = load_raw_data(PROJECT_ROOT / data_cfg["raw_path"])
    clean_df = validate_data(raw_df, known_categories=data_cfg.get("known_categories"))
    featured_df = add_engineered_features(clean_df)

    target = data_cfg["target"]
    drop_columns = [c for c in data_cfg.get("drop_columns", []) if c in featured_df.columns]
    numeric_cols = featured_df.drop(columns=[target] + drop_columns).select_dtypes(include="number").columns

    means = featured_df[numeric_cols].mean().to_dict()
    correlations = featured_df[numeric_cols].corrwith(featured_df[target]).to_dict()
    return means, correlations


def _aggregate_importances(feature_names, importances, known_raw_features) -> dict[str, float]:
    aggregated: dict[str, float] = {}
    for name, importance in zip(feature_names, importances):
        raw_name = name.split("__", 1)[-1]
        matched = raw_name
        for original in known_raw_features:
            if raw_name == original or raw_name.startswith(original + "_"):
                matched = original
                break
        aggregated[matched] = aggregated.get(matched, 0.0) + float(importance)
    return aggregated


def explain_prediction(record: dict, top_k: int = TOP_K) -> list[dict]:
    pipeline = load_pipeline()
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]

    means, correlations = _training_reference()
    feature_names = preprocessor.get_feature_names_out()
    importances = model.feature_importances_
    aggregated = _aggregate_importances(feature_names, importances, list(means.keys()) + ["Occupation", "City_Tier"])

    featured = add_engineered_features(pd.DataFrame([record]))
    ranked = sorted(aggregated.items(), key=lambda item: item[1], reverse=True)[:top_k]

    explanation = []
    for feature, impact in ranked:
        direction = "positive"
        if feature in means and feature in correlations and feature in featured.columns:
            value = featured[feature].iloc[0]
            above_mean = value > means[feature]
            positive_correlation = correlations[feature] > 0
            direction = "positive" if above_mean == positive_correlation else "negative"
        explanation.append({"feature": feature, "impact": round(impact, 4), "direction": direction})

    return explanation
