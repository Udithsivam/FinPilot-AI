from src.rag.knowledge_base import load_chunks
from src.rag.retrieval import retrieve


def test_load_chunks_finds_documents_with_metadata():
    chunks = load_chunks()
    assert len(chunks) > 10
    ids = {c.document_id for c in chunks}
    assert "emergency_fund" in ids
    assert "budgeting" in ids
    for chunk in chunks:
        assert chunk.title
        assert chunk.source
        assert chunk.text


def test_retrieve_finds_relevant_document():
    results = retrieve("What is an emergency fund?", top_k=4)
    assert any(r["document_id"] == "emergency_fund" for r in results)
    for r in results:
        assert r["source"]
        assert r["title"]
        assert 0.0 <= r["score"] <= 1.0


def test_retrieve_returns_empty_for_blank_query():
    assert retrieve("") == []
    assert retrieve("   ") == []


def test_retrieve_returns_empty_for_irrelevant_query():
    # Nonsense text sharing no vocabulary with any knowledge chunk.
    results = retrieve("xyzzyx qwerty12345 zzzzznotarealword")
    assert results == []
