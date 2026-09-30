"""MLflow Model Registry abstraction: candidate -> validated -> production
-> archived lifecycle, on top of MLflow's own registry (aliases/tags),
plus a controlled local fallback.

MLflow's model registry has built-in stage/alias concepts, but this
project's lifecycle (candidate -> validated -> production -> archived) is
an explicit project decision, not MLflow's default vocabulary, so it's
tracked as an MLflow tag ("lifecycle_stage") on each model VERSION rather
than repurposing MLflow's own aliasing scheme. This keeps the four
states — and the rules about which transitions are legal — fully under
this project's control and auditable via plain MLflow version tags.

Fallback behavior: if the MLflow tracking server / registry database is
unavailable, `get_production_model()` falls back to loading the local
.pkl artifact directly (the same file DVC tracks) — but it returns
`source="local_fallback"` explicitly rather than silently pretending it
came from the registry, per the "the application must clearly know
whether it loaded registry model or local fallback" requirement.
"""

from pathlib import Path

import joblib
import mlflow
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VALID_STAGES = ["candidate", "validated", "production", "archived"]

_VALID_TRANSITIONS = {
    "candidate": {"validated"},
    "validated": {"production", "archived"},
    "production": {"archived"},
    "archived": set(),
}

LOCAL_FALLBACK_PATHS = {
    "finpilot-savings-predictor": PROJECT_ROOT / "models" / "savings_prediction_pipeline.pkl",
    "finpilot-transaction-categorizer": PROJECT_ROOT / "models" / "transaction_categorizer_pipeline.pkl",
    "finpilot-expense-forecaster": PROJECT_ROOT / "models" / "expense_forecast_pipeline.pkl",
    "finpilot-cashflow-forecaster": PROJECT_ROOT / "models" / "cashflow_forecast_pipeline.pkl",
}


class InvalidTransitionError(Exception):
    pass


def _client() -> MlflowClient:
    mlflow.set_tracking_uri(f"sqlite:///{(PROJECT_ROOT / 'mlflow.db').as_posix()}")
    return MlflowClient()


def _stage_of(client: MlflowClient, name: str, version: str) -> str | None:
    mv = client.get_model_version(name, version)
    return (mv.tags or {}).get("lifecycle_stage")


def list_versions(name: str) -> list[dict]:
    """All versions of a registered model with their lifecycle stage and
    metadata, newest first. Returns [] (not an error) if the registry is
    unreachable or the model doesn't exist yet."""
    try:
        client = _client()
        versions = client.search_model_versions(f"name='{name}'")
    except MlflowException:
        return []

    results = []
    for v in sorted(versions, key=lambda v: int(v.version), reverse=True):
        results.append(
            {
                "name": name,
                "version": v.version,
                "run_id": v.run_id,
                "lifecycle_stage": (v.tags or {}).get("lifecycle_stage", "candidate"),
                "created_at": v.creation_timestamp,
            }
        )
    return results


def set_lifecycle_stage(name: str, version: str, target_stage: str) -> dict:
    """Transition one model version's lifecycle stage, enforcing the
    candidate -> validated -> production -> archived state machine.

    Promoting a version to "production" automatically archives whatever
    version currently holds "production" for the same model (never two
    simultaneous production versions, and the previous production version
    is archived, never deleted — its artifact and metadata are untouched).
    """
    if target_stage not in VALID_STAGES:
        raise ValueError(f"Unknown lifecycle stage: {target_stage}")

    client = _client()
    current_stage = _stage_of(client, name, version) or "candidate"

    if target_stage not in _VALID_TRANSITIONS.get(current_stage, set()) and target_stage != current_stage:
        raise InvalidTransitionError(f"Cannot transition {name} v{version} from {current_stage} to {target_stage}")

    if target_stage == "production":
        for v in list_versions(name):
            if v["version"] != version and v["lifecycle_stage"] == "production":
                client.set_model_version_tag(name, v["version"], "lifecycle_stage", "archived")

    client.set_model_version_tag(name, version, "lifecycle_stage", target_stage)
    return {"name": name, "version": version, "lifecycle_stage": target_stage, "previous_stage": current_stage}


def get_production_version(name: str) -> dict | None:
    for v in list_versions(name):
        if v["lifecycle_stage"] == "production":
            return v
    return None


def rollback_to_version(name: str, target_version: str) -> dict:
    """Roll back: whatever version is currently "production" becomes
    "archived", and `target_version` (which must currently be "archived",
    i.e. a previous production version) becomes "production". No artifact
    is ever deleted — both versions' history and metadata are preserved,
    only the lifecycle_stage tag changes."""
    client = _client()
    target_stage = _stage_of(client, name, target_version)
    if target_stage != "archived":
        raise InvalidTransitionError(
            f"Can only roll back to a previously-archived version; {name} v{target_version} is '{target_stage}'"
        )

    current_production = get_production_version(name)
    if current_production is not None:
        client.set_model_version_tag(name, current_production["version"], "lifecycle_stage", "archived")

    client.set_model_version_tag(name, target_version, "lifecycle_stage", "production")
    return {
        "name": name,
        "rolled_back_to": target_version,
        "previous_production": current_production["version"] if current_production else None,
    }


def load_production_model(name: str):
    """Load the current production model artifact.

    Returns (model, metadata) where metadata always includes `source`:
    "registry" if loaded from the MLflow-registered production version,
    or "local_fallback" if the registry was unreachable/empty and the
    local .pkl artifact was used instead — never silently one or the
    other.
    """
    production = get_production_version(name)
    if production is not None:
        try:
            model_uri = f"models:/{name}/{production['version']}"
            model = mlflow.sklearn.load_model(model_uri)
            return model, {
                "source": "registry",
                "model_version": production["version"],
                "run_id": production["run_id"],
            }
        except MlflowException:
            pass

    fallback_path = LOCAL_FALLBACK_PATHS.get(name)
    if fallback_path is None or not fallback_path.exists():
        raise FileNotFoundError(f"No production registry version and no local fallback artifact for {name}")

    model = joblib.load(fallback_path)
    return model, {"source": "local_fallback", "model_version": None, "run_id": None}
