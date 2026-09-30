"""Train the transaction-categorization model.

data/raw/finpilot_transactions.csv (SYNTHETIC, see
scripts/generate_transaction_data.py) -> validate -> text features ->
TF-IDF + LogisticRegression -> evaluate -> MLflow -> save artifact.

Split strategy: stratified random split, NOT chronological. This is
deliberate, not an oversight — unlike expense forecasting or cash-flow
prediction (which predict a future value from past values, and would
leak the future into training under a random split), categorizing a
single transaction from its own merchant/description text has no
temporal dependency: transaction #500's text doesn't inform transaction
#4000's label. A stratified split (preserving each category's
proportion in both splits) is the correct choice here specifically
because rare categories (e.g. Insurance, Loan/Debt) would otherwise be
under-represented in a small test set.

Usage:
    python -m src.categorization.train
"""

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from src.categorization.features import build_text_feature
from src.pipeline.tracking import current_git_commit

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "finpilot_transactions.csv"
PIPELINE_PATH = PROJECT_ROOT / "models" / "transaction_categorizer_pipeline.pkl"
METRICS_PATH = PROJECT_ROOT / "reports" / "categorization_metrics.json"

EXPERIMENT_NAME = "finpilot-transaction-categorization"
REGISTERED_MODEL_NAME = "finpilot-transaction-categorizer"

RANDOM_STATE = 42
TEST_SIZE = 0.2


def load_and_validate() -> pd.DataFrame:
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"{DATA_PATH} not found. Generate it first: python -m scripts.generate_transaction_data"
        )
    df = pd.read_csv(DATA_PATH)

    issues = []
    if (df["amount"] <= 0).any():
        issues.append("non-positive amount values found")
    expense = df[df["transaction_type"] == "expense"]
    if expense["category"].isna().any() or expense["subcategory"].isna().any():
        issues.append("expense rows with missing category/subcategory")
    if issues:
        raise ValueError("Data validation failed: " + "; ".join(issues))

    return df


def run_training() -> dict:
    df = load_and_validate()
    expense = df[df["transaction_type"] == "expense"].copy()

    expense["label"] = expense["category"] + " > " + expense["subcategory"]
    text = build_text_feature(expense["merchant"], expense["description"])

    X_train, X_test, y_train, y_test = train_test_split(
        text, expense["label"], test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=expense["label"]
    )
    labels = sorted(expense["label"].unique())

    # Two candidates over the same TF-IDF features: the existing
    # LogisticRegression baseline, and LinearSVC (wrapped in
    # CalibratedClassifierCV so it can still expose predict_proba, which
    # src/categorization/predict.py's confidence score and needs_review
    # flag depend on). Selection is by macro-F1 on the held-out test set,
    # not by which algorithm sounds more advanced — see README for why a
    # full sentence-transformer embedding classifier was not adopted
    # (heavy new dependency, no meaningful gain expected on a small
    # 16-class synthetic vocabulary).
    candidates = {
        "LogisticRegression": Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1, 2))),
                ("model", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
            ]
        ),
        "LinearSVC_calibrated": Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1, 2))),
                (
                    "model",
                    CalibratedClassifierCV(
                        LinearSVC(random_state=RANDOM_STATE, max_iter=5000), method="sigmoid", cv=3
                    ),
                ),
            ]
        ),
    }

    candidate_results = {}
    for name, candidate_pipeline in candidates.items():
        candidate_pipeline.fit(X_train, y_train)
        candidate_predictions = candidate_pipeline.predict(X_test)
        c_accuracy = accuracy_score(y_test, candidate_predictions)
        c_precision, c_recall, c_f1, _ = precision_recall_fscore_support(
            y_test, candidate_predictions, average="macro", zero_division=0
        )
        candidate_results[name] = {
            "pipeline": candidate_pipeline,
            "predictions": candidate_predictions,
            "metrics": {
                "accuracy": c_accuracy,
                "macro_precision": c_precision,
                "macro_recall": c_recall,
                "macro_f1": c_f1,
            },
        }

    best_name = max(candidate_results, key=lambda n: candidate_results[n]["metrics"]["macro_f1"])
    pipeline = candidate_results[best_name]["pipeline"]
    predictions = candidate_results[best_name]["predictions"]
    accuracy = candidate_results[best_name]["metrics"]["accuracy"]
    precision = candidate_results[best_name]["metrics"]["macro_precision"]
    recall = candidate_results[best_name]["metrics"]["macro_recall"]
    f1 = candidate_results[best_name]["metrics"]["macro_f1"]

    conf_matrix = confusion_matrix(y_test, predictions, labels=labels).tolist()
    report = classification_report(y_test, predictions, labels=labels, zero_division=0, output_dict=True)

    metrics = {
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "n_classes": len(labels),
        "selected_model": best_name,
        "candidates": {name: r["metrics"] for name, r in candidate_results.items()},
        "labels": labels,
        "confusion_matrix": conf_matrix,
        "per_class_report": report,
    }

    PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, PIPELINE_PATH)

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    mlflow.set_tracking_uri(f"sqlite:///{(PROJECT_ROOT / 'mlflow.db').as_posix()}")
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name="categorization_training"):
        git_commit = current_git_commit(PROJECT_ROOT)
        if git_commit:
            mlflow.set_tag("git_commit", git_commit)
        mlflow.log_params(
            {
                "max_features": 2000,
                "ngram_range": "(1, 2)",
                "n_train": len(X_train),
                "n_test": len(X_test),
                "n_classes": len(labels),
                "test_size": TEST_SIZE,
                "random_state": RANDOM_STATE,
            }
        )
        for name, result in candidate_results.items():
            with mlflow.start_run(run_name=name, nested=True):
                mlflow.log_param("model_type", name)
                mlflow.log_metrics(result["metrics"])

        mlflow.set_tag("selected_model", best_name)
        mlflow.log_metrics(
            {
                "accuracy": accuracy,
                "macro_precision": precision,
                "macro_recall": recall,
                "macro_f1": f1,
            }
        )
        mlflow.sklearn.log_model(
            pipeline,
            name="model",
            registered_model_name=REGISTERED_MODEL_NAME,
            serialization_format="cloudpickle",
        )

    return metrics


def main() -> None:
    metrics = run_training()
    print(
        json.dumps(
            {k: v for k, v in metrics.items() if k not in ("confusion_matrix", "per_class_report", "labels")},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
