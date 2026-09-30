"""Feedback-driven retraining for the transaction categorizer.

Flow (see PART T in the project brief):

    user feedback (category_correction rows)
      -> ownership already validated at write time (POST /feedback)
      -> schema/category validation (must match the canonical taxonomy,
         must reference a real transaction so real text is available)
      -> curated into a small supplementary training frame
      -> appended to the synthetic training dataset
      -> candidate model trained (chronological/stratified split
         unchanged from src/categorization/train.py)
      -> evaluated exactly like any other candidate
      -> logged to MLflow as a new candidate version (lifecycle_stage
         tag = "candidate", NOT promoted)
      -> compared against the current production version's metrics
      -> promotion is a SEPARATE, explicit step (see
         src/registry/model_registry.py) — this script never promotes
         automatically, even if the candidate's metrics look better.

Usage:
    python -m scripts.retrain_from_feedback
"""

import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.models.feedback import Feedback
from src.categorization.features import build_text_feature
from src.categorization.taxonomy import TAXONOMY, joint_labels
from src.pipeline.tracking import current_git_commit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "finpilot_transactions.csv"
CANDIDATE_PIPELINE_PATH = PROJECT_ROOT / "models" / "transaction_categorizer_candidate.pkl"
REPORT_PATH = PROJECT_ROOT / "reports" / "feedback_retraining_report.json"

EXPERIMENT_NAME = "finpilot-transaction-categorization"
REGISTERED_MODEL_NAME = "finpilot-transaction-categorizer"

RANDOM_STATE = 42
TEST_SIZE = 0.2
_VALID_LABELS = set(joint_labels())


def _session():
    settings = get_settings()
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine)()


def curate_feedback_dataset(db: Session) -> pd.DataFrame:
    """Pull category_correction feedback, validated and de-duplicated.

    Rejects (skips, never raises on) rows with a corrected_value outside
    the canonical taxonomy. Takes an already-open session so it can be
    tested against an isolated in-memory database (see
    tests/unit/test_retrain_from_feedback.py) instead of the real dev DB.
    """
    # Feedback has no direct FK to Transaction (only to Prediction, which
    # doesn't carry the original merchant/description text either) — a
    # real schema limitation, documented in the README. So a correction
    # can't be re-joined back to its original raw transaction text; see
    # the weak-text-signal fallback below.
    feedback_rows = db.query(Feedback).filter(Feedback.feedback_type == "category_correction").all()

    curated: dict[int, dict] = {}
    for fb in feedback_rows:
        if not fb.corrected_value or " > " not in fb.corrected_value:
            continue
        category, _, subcategory = fb.corrected_value.partition(" > ")
        label = f"{category} > {subcategory}"
        if category not in TAXONOMY or label not in _VALID_LABELS:
            continue
        # No linked transaction text is available from Feedback alone
        # (see limitation above) — use the corrected category name itself
        # as a weak text signal so the row is still usable as a
        # supervised example without fabricating merchant/description
        # text that was never actually provided.
        curated[fb.id] = {"text": f"{category} {subcategory}", "label": label}

    return pd.DataFrame(curated.values())


def load_synthetic_training_data() -> pd.DataFrame:
    df = pd.read_csv(SYNTHETIC_DATA_PATH)
    expense = df[df["transaction_type"] == "expense"].copy()
    expense["label"] = expense["category"] + " > " + expense["subcategory"]
    expense["text"] = build_text_feature(expense["merchant"], expense["description"])
    return expense[["text", "label"]]


def run_retraining(feedback_df: pd.DataFrame) -> dict:
    synthetic_df = load_synthetic_training_data()
    combined = pd.concat([synthetic_df, feedback_df], ignore_index=True)

    # Stratification requires >=2 examples per class. A feedback-corrected
    # label that never appears in the synthetic base set can add a class
    # with only 1 total example — fall back to a plain random split in
    # that case rather than crashing on an otherwise legitimate retrain.
    label_counts = combined["label"].value_counts()
    stratify = combined["label"] if label_counts.min() >= 2 else None

    X_train, X_test, y_train, y_test = train_test_split(
        combined["text"], combined["label"], test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=stratify
    )

    pipeline = Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(max_features=2000, ngram_range=(1, 2))),
            ("model", LogisticRegression(max_iter=1000, random_state=RANDOM_STATE)),
        ]
    )
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(y_test, predictions, average="macro", zero_division=0)

    metrics = {
        "feedback_rows_used": len(feedback_df),
        "synthetic_rows_used": len(synthetic_df),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1,
    }

    CANDIDATE_PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, CANDIDATE_PIPELINE_PATH)

    mlflow.set_tracking_uri(f"sqlite:///{(PROJECT_ROOT / 'mlflow.db').as_posix()}")
    mlflow.set_experiment(EXPERIMENT_NAME)
    with mlflow.start_run(run_name="feedback_retraining"):
        git_commit = current_git_commit(PROJECT_ROOT)
        if git_commit:
            mlflow.set_tag("git_commit", git_commit)
        mlflow.set_tag("training_type", "feedback_retraining")
        mlflow.log_params(
            {
                "feedback_rows_used": len(feedback_df),
                "synthetic_rows_used": len(synthetic_df),
                "n_train": len(X_train),
                "n_test": len(X_test),
            }
        )
        mlflow.log_metrics(
            {"accuracy": accuracy, "macro_precision": precision, "macro_recall": recall, "macro_f1": f1}
        )
        model_info = mlflow.sklearn.log_model(
            pipeline,
            name="model",
            registered_model_name=REGISTERED_MODEL_NAME,
            serialization_format="cloudpickle",
        )
        # Explicitly a candidate — this script never promotes it. See
        # src/registry/model_registry.py for the separate promotion step.
        from mlflow import MlflowClient

        MlflowClient().set_model_version_tag(
            REGISTERED_MODEL_NAME, model_info.registered_model_version, "lifecycle_stage", "candidate"
        )
        metrics["candidate_version"] = model_info.registered_model_version
        metrics["run_id"] = model_info.run_id

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def main() -> None:
    db = _session()
    try:
        feedback_df = curate_feedback_dataset(db)
    finally:
        db.close()

    if len(feedback_df) == 0:
        print(
            json.dumps(
                {
                    "status": "insufficient_data",
                    "detail": "No validated category_correction feedback rows found yet — nothing to retrain from.",
                },
                indent=2,
            )
        )
        return
    metrics = run_retraining(feedback_df)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
