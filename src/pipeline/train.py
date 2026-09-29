"""End-to-end training pipeline entrypoint.

Usage:
    python -m src.pipeline.train
"""

import json
from pathlib import Path

import joblib
import yaml
from sklearn.model_selection import train_test_split

from src.data.load_data import load_raw_data
from src.data.validate_data import validate_data
from src.features.build_features import add_engineered_features
from src.pipeline.preprocessing import build_preprocessor
from src.pipeline.tracking import configure_mlflow, log_training_run
from src.training.train_model import (
    build_candidate_models,
    select_best,
    train_and_evaluate_candidates,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_params(path: Path = PROJECT_ROOT / "params.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def run_training(params: dict) -> dict:
    data_cfg = params["data"]
    model_cfg = params["model"]
    artifact_cfg = params["artifacts"]

    raw_df = load_raw_data(PROJECT_ROOT / data_cfg["raw_path"])
    clean_df = validate_data(raw_df, known_categories=data_cfg.get("known_categories"))
    featured_df = add_engineered_features(clean_df)

    target = data_cfg["target"]
    drop_columns = [c for c in data_cfg.get("drop_columns", []) if c in featured_df.columns]
    X = featured_df.drop(columns=[target] + drop_columns)
    y = featured_df[target]

    categorical_features = data_cfg["categorical_columns"]
    numeric_features = [c for c in X.columns if c not in categorical_features]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=data_cfg["test_size"], random_state=data_cfg["random_state"]
    )

    preprocessor = build_preprocessor(numeric_features, categorical_features)
    candidates = build_candidate_models(model_cfg["candidates"], model_cfg["random_state"])
    results = train_and_evaluate_candidates(
        candidates, preprocessor, X_train, y_train, X_test, y_test
    )

    best_name = select_best(results, metric=model_cfg["selection_metric"])
    best_pipeline = results[best_name]["pipeline"]

    configure_mlflow(PROJECT_ROOT)
    log_training_run(
        PROJECT_ROOT,
        run_params={
            "target": target,
            "test_size": data_cfg["test_size"],
            "random_state": data_cfg["random_state"],
            "n_train": len(X_train),
            "n_test": len(X_test),
        },
        results=results,
        best_name=best_name,
    )

    pipeline_path = PROJECT_ROOT / artifact_cfg["pipeline_path"]
    pipeline_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(best_pipeline, pipeline_path)

    metrics_report = {name: r["metrics"] for name, r in results.items()}
    metrics_report["_selected_model"] = best_name

    metrics_path = PROJECT_ROOT / artifact_cfg["metrics_path"]
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics_report, f, indent=2)

    return metrics_report


def main():
    params = load_params()
    metrics_report = run_training(params)
    print(json.dumps(metrics_report, indent=2))


if __name__ == "__main__":
    main()
