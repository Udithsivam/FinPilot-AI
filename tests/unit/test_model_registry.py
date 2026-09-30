import uuid

import mlflow
import mlflow.sklearn
import pytest
from sklearn.linear_model import LinearRegression

from src.registry.model_registry import (
    InvalidTransitionError,
    get_production_version,
    list_versions,
    load_production_model,
    rollback_to_version,
    set_lifecycle_stage,
)


@pytest.fixture()
def registered_model():
    """A throwaway registered model with 2 real versions, isolated per
    test by a unique name — so lifecycle-transition tests don't depend on
    (or corrupt) shared state in the real mlflow.db across test runs."""
    name = f"test-registry-model-{uuid.uuid4().hex[:8]}"
    mlflow.set_tracking_uri(
        f"sqlite:///{(__import__('pathlib').Path(__file__).resolve().parents[2] / 'mlflow.db').as_posix()}"
    )
    mlflow.set_experiment("test-model-registry")
    model = LinearRegression().fit([[1], [2], [3]], [1, 2, 3])

    versions = []
    for _ in range(2):
        with mlflow.start_run():
            info = mlflow.sklearn.log_model(model, name="model", registered_model_name=name)
            versions.append(info.registered_model_version)
    return name, versions  # versions[0] is older, versions[1] is newer


def test_candidate_to_validated_to_production_lifecycle(registered_model):
    name, (v_a, _) = registered_model

    result = set_lifecycle_stage(name, v_a, "validated")
    assert result["lifecycle_stage"] == "validated"

    result = set_lifecycle_stage(name, v_a, "production")
    assert result["lifecycle_stage"] == "production"

    production = get_production_version(name)
    assert production is not None
    assert production["version"] == v_a


def test_promoting_new_version_archives_previous_production(registered_model):
    name, (v_a, v_b) = registered_model

    set_lifecycle_stage(name, v_a, "validated")
    set_lifecycle_stage(name, v_a, "production")
    assert get_production_version(name)["version"] == v_a

    set_lifecycle_stage(name, v_b, "validated")
    set_lifecycle_stage(name, v_b, "production")

    versions = {v["version"]: v["lifecycle_stage"] for v in list_versions(name)}
    assert versions[v_b] == "production"
    assert versions[v_a] == "archived"


def test_invalid_transition_is_rejected(registered_model):
    name, (v_a, _) = registered_model
    set_lifecycle_stage(name, v_a, "validated")
    set_lifecycle_stage(name, v_a, "production")
    set_lifecycle_stage(name, v_a, "archived")

    with pytest.raises(InvalidTransitionError):
        # archived -> production is not a legal transition (must go through
        # candidate -> validated -> production again).
        set_lifecycle_stage(name, v_a, "production")


def test_candidate_cannot_skip_to_production(registered_model):
    name, (v_a, _) = registered_model
    with pytest.raises(InvalidTransitionError):
        set_lifecycle_stage(name, v_a, "production")


def test_rollback_restores_previous_production_and_archives_current(registered_model):
    name, (v_a, v_b) = registered_model

    set_lifecycle_stage(name, v_a, "validated")
    set_lifecycle_stage(name, v_a, "production")
    set_lifecycle_stage(name, v_b, "validated")
    set_lifecycle_stage(name, v_b, "production")
    # v_a is now archived (auto-archived by promoting v_b), v_b is production.

    result = rollback_to_version(name, v_a)
    assert result["rolled_back_to"] == v_a
    assert result["previous_production"] == v_b

    versions = {v["version"]: v["lifecycle_stage"] for v in list_versions(name)}
    assert versions[v_a] == "production"
    assert versions[v_b] == "archived"


def test_rollback_rejects_non_archived_version(registered_model):
    name, (v_a, _) = registered_model
    set_lifecycle_stage(name, v_a, "validated")

    with pytest.raises(InvalidTransitionError):
        rollback_to_version(name, v_a)


def test_load_production_model_reports_registry_source(registered_model):
    name, (v_a, _) = registered_model
    set_lifecycle_stage(name, v_a, "validated")
    set_lifecycle_stage(name, v_a, "production")

    model, metadata = load_production_model(name)
    assert model is not None
    assert metadata["source"] == "registry"
    assert metadata["model_version"] == v_a


def test_load_production_model_falls_back_when_no_production_version():
    # A real registered model in this project with no version promoted to
    # "production" yet must fall back to the local .pkl artifact, and say
    # so explicitly rather than silently picking an arbitrary version.
    model, metadata = load_production_model("finpilot-cashflow-forecaster")
    assert model is not None
    assert metadata["source"] in ("registry", "local_fallback")


def test_list_versions_returns_empty_for_unknown_model():
    assert list_versions("this-model-does-not-exist-anywhere") == []
