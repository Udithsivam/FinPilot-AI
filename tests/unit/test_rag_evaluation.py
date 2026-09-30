from src.rag.evaluation import evaluate_retrieval


def test_evaluate_retrieval_reports_real_hit_rate():
    report = evaluate_retrieval(top_k=4)
    assert report["n_questions"] == len(report["results"])
    assert 0.0 <= report["hit_at_k"] <= 1.0
    assert report["hits"] == sum(1 for r in report["results"] if r["hit"])
    assert "limitation" in report
