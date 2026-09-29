"""MLflow experiment tracking for the training pipeline.

Tracking and the model registry both use a local SQLite store
(mlflow.db) rather than the default file store, since MLflow's model
registry requires a database-backed backend.
"""

import subprocess
from pathlib import Path

import mlflow
import mlflow.sklearn

EXPERIMENT_NAME = "finpilot-savings-prediction"
REGISTERED_MODEL_NAME = "finpilot-savings-predictor"


def configure_mlflow(project_root: Path) -> None:
    mlflow.set_tracking_uri(f"sqlite:///{(project_root / 'mlflow.db').as_posix()}")
    mlflow.set_experiment(EXPERIMENT_NAME)


def current_git_commit(project_root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def log_training_run(project_root: Path, run_params: dict, results: dict, best_name: str) -> None:
    """Log one parent run for the training pipeline plus a nested run per
    candidate model, and register the selected model as a new version of
    REGISTERED_MODEL_NAME."""
    with mlflow.start_run(run_name="training_pipeline"):
        mlflow.log_params(run_params)
        git_commit = current_git_commit(project_root)
        if git_commit:
            mlflow.set_tag("git_commit", git_commit)

        for name, result in results.items():
            with mlflow.start_run(run_name=name, nested=True):
                mlflow.log_param("model_type", name)
                mlflow.log_metrics(result["metrics"])
                # cloudpickle instead of the skops default: these models are
                # freshly trained in-process, not loaded from an untrusted
                # file, so skops's tree-structure audit has nothing to buy us.
                mlflow.sklearn.log_model(
                    result["pipeline"], name="model", serialization_format="cloudpickle"
                )

        best_metrics = results[best_name]["metrics"]
        mlflow.set_tag("selected_model", best_name)
        mlflow.log_metrics({f"best_{k}": v for k, v in best_metrics.items()})
        mlflow.sklearn.log_model(
            results[best_name]["pipeline"],
            name="best_model",
            registered_model_name=REGISTERED_MODEL_NAME,
            serialization_format="cloudpickle",
        )
