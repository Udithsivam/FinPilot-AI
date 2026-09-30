"""Inference for the transaction-categorization model.

Mirrors src/pipeline/predict.py's caching pattern exactly (same
lru_cache + content-hash-as-version approach), for the same reasons:
avoid re-reading the artifact from disk on every request, and expose a
verifiable, non-fabricated model_version.
"""

import hashlib
from functools import lru_cache
from pathlib import Path

import joblib

from src.categorization.features import build_text_feature
from src.categorization.taxonomy import split_joint_label

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PIPELINE_PATH = PROJECT_ROOT / "models" / "transaction_categorizer_pipeline.pkl"


@lru_cache(maxsize=4)
def _load_pipeline_cached(path: Path):
    return joblib.load(path)


def load_pipeline(path: Path = DEFAULT_PIPELINE_PATH):
    return _load_pipeline_cached(path)


def clear_pipeline_cache() -> None:
    _load_pipeline_cached.cache_clear()
    get_model_metadata.cache_clear()


@lru_cache(maxsize=4)
def get_model_metadata(path: Path = DEFAULT_PIPELINE_PATH) -> dict:
    pipeline = load_pipeline(path)
    model_type = type(pipeline.named_steps["model"]).__name__
    file_hash = hashlib.md5(Path(path).read_bytes(), usedforsecurity=False).hexdigest()[:8]
    return {"model_type": model_type, "model_version": file_hash}


def categorize_transaction(merchant: str | None, description: str | None) -> dict:
    """Predict category/subcategory for one transaction's text.

    Returns confidence as the model's own predicted probability for the
    chosen label (real, from predict_proba — not a placeholder).
    """
    pipeline = load_pipeline()
    text = build_text_feature(merchant or "", description or "")

    predicted_label = pipeline.predict([text])[0]
    probabilities = pipeline.predict_proba([text])[0]
    confidence = float(max(probabilities))
    category, subcategory = split_joint_label(predicted_label)

    metadata = get_model_metadata()
    return {
        "category": category,
        "subcategory": subcategory,
        "confidence": confidence,
        "model_version": metadata["model_version"],
    }
