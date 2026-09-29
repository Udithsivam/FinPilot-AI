"""Candidate model definitions and training/evaluation helpers."""

from sklearn.base import RegressorMixin
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeRegressor

from src.evaluation.metrics import regression_metrics

MODEL_REGISTRY = {
    "linear_regression": lambda random_state: LinearRegression(),
    "decision_tree": lambda random_state: DecisionTreeRegressor(random_state=random_state),
    "random_forest": lambda random_state: RandomForestRegressor(random_state=random_state),
    "gradient_boosting": lambda random_state: GradientBoostingRegressor(random_state=random_state),
}


def build_candidate_models(names: list[str], random_state: int) -> dict[str, RegressorMixin]:
    unknown = set(names) - set(MODEL_REGISTRY)
    if unknown:
        raise ValueError(f"Unknown model candidates: {sorted(unknown)}")
    return {name: MODEL_REGISTRY[name](random_state) for name in names}


def train_and_evaluate_candidates(
    candidates: dict[str, RegressorMixin],
    preprocessor,
    X_train,
    y_train,
    X_test,
    y_test,
) -> dict[str, dict]:
    """Fit each candidate model behind the shared preprocessor and score it.

    Returns a dict keyed by model name with the fitted pipeline and its
    held-out metrics, so the caller can select the best one.
    """
    results = {}
    for name, estimator in candidates.items():
        pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", estimator)])
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
        results[name] = {
            "pipeline": pipeline,
            "metrics": regression_metrics(y_test, predictions),
        }
    return results


def select_best(results: dict[str, dict], metric: str = "r2") -> str:
    higher_is_better = metric == "r2"
    return max(
        results,
        key=lambda name: results[name]["metrics"][metric] * (1 if higher_is_better else -1),
    )
