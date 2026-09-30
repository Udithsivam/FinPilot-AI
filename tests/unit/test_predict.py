from src.pipeline import predict as predict_module
from src.pipeline.predict import clear_pipeline_cache, load_pipeline


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


def test_clear_pipeline_cache_forces_reload(monkeypatch):
    clear_pipeline_cache()
    calls = []

    def fake_joblib_load(path):
        calls.append(path)
        return object()

    monkeypatch.setattr(predict_module.joblib, "load", fake_joblib_load)

    first = load_pipeline(predict_module.DEFAULT_PIPELINE_PATH)
    clear_pipeline_cache()
    second = load_pipeline(predict_module.DEFAULT_PIPELINE_PATH)

    assert first is not second
    assert len(calls) == 2
    clear_pipeline_cache()
