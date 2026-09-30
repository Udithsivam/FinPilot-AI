"""TF-IDF retrieval over the curated knowledge-base chunks.

Same reasoning as src/search/semantic_search.py: TF-IDF + cosine
similarity rather than a sentence-transformer embedding model, to avoid
a multi-GB torch dependency for a ~50-chunk local knowledge base where
the retrieval quality difference would not be visible at this scale.
This is a real (if lexical) semantic vector space, not keyword-only
matching — see docstring in semantic_search.py for the fuller argument.
Swapping in sentence-transformers later only requires changing this
module; callers only see `retrieve(query, top_k)`.

The index is built once and cached (`lru_cache`) — rebuilding a TF-IDF
matrix over the whole knowledge base on every request would be wasted
work, since the knowledge base only changes when someone edits
data/knowledge/ and restarts the process.
"""

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.rag.knowledge_base import load_chunks

MIN_SIMILARITY = 0.05


@lru_cache(maxsize=1)
def _build_index():
    chunks = load_chunks()
    if not chunks:
        return [], None, None
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
    matrix = vectorizer.fit_transform([c.text for c in chunks])
    return chunks, vectorizer, matrix


def clear_index_cache() -> None:
    _build_index.cache_clear()


def retrieve(query: str, top_k: int = 4) -> list[dict]:
    """Retrieve the top_k most relevant knowledge chunks for `query`.

    Returns an empty list if the knowledge base is empty or nothing
    clears the minimum similarity threshold — never a fabricated "closest
    match" when nothing is actually relevant.
    """
    if not query or not query.strip():
        return []

    chunks, vectorizer, matrix = _build_index()
    if not chunks:
        return []

    query_vector = vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, matrix)[0]
    ranked_indices = sorted(range(len(chunks)), key=lambda i: similarities[i], reverse=True)

    results = []
    for i in ranked_indices[:top_k]:
        if similarities[i] < MIN_SIMILARITY:
            continue
        chunk = chunks[i]
        results.append(
            {
                "document_id": chunk.document_id,
                "chunk_id": chunk.chunk_id,
                "title": chunk.title,
                "source": chunk.source,
                "topic": chunk.topic,
                "text": chunk.text,
                "score": round(float(similarities[i]), 4),
            }
        )
    return results
