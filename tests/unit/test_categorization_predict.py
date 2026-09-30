from src.categorization import predict as predict_module
from src.categorization.predict import categorize_transaction, clear_pipeline_cache, load_pipeline
from src.categorization.taxonomy import TAXONOMY


def test_load_pipeline_is_cached(monkeypatch):
    clear_pipeline_cache()
    calls = []

    def fake_joblib_load(path):
        calls.append(path)
        return object()

    monkeypatch.setattr(predict_module.joblib, "load", fake_joblib_load)
    first = load_pipeline(predict_module.DEFAULT_PIPELINE_PATH)
    second = load_pipeline(predict_module.DEFAULT_PIPELINE_PATH)

    assert first is second
    assert len(calls) == 1
    clear_pipeline_cache()


def test_categorize_transaction_returns_valid_taxonomy_label():
    result = categorize_transaction("Swiggy", "Swiggy Order")
    assert result["category"] in TAXONOMY
    assert result["subcategory"] in TAXONOMY[result["category"]]
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["model_version"]
    assert isinstance(result["needs_review"], bool)
    assert result["needs_review"] == (result["confidence"] < 0.5)


def test_categorize_transaction_handles_missing_merchant():
    result = categorize_transaction(None, "Monthly Rent Payment")
    assert result["category"] == "Housing"
    assert result["subcategory"] == "Rent"
