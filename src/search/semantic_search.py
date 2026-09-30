"""Semantic search over one user's own transactions.

Uses TF-IDF + cosine similarity rather than a transformer sentence-
embedding model: the corpus being searched is a single user's own
transaction text (typically tens to a few hundred short strings), so a
heavy embedding model (sentence-transformers pulls in a multi-GB torch
dependency) buys little over a lexical/semantic vector space model for
this scale, while meaningfully slowing every request. TF-IDF vectors ARE
a real (if shallow) semantic representation — cosine similarity in that
space finds transactions that share vocabulary/topic with the query,
not just exact substring matches (e.g. "food delivery" query matches
"Swiggy Order", "Zomato Bill" via shared/co-occurring terms), which is
the actual requirement here. There is no persistent index (FAISS or
otherwise): the vector space is rebuilt per request from that one user's
transactions, which at this scale is fast and keeps the system simple
(no index-staleness problem to manage).

CRITICAL: the corpus is always exactly one user's own transactions,
built from a caller-supplied DataFrame already filtered by user_id, so
cross-user leakage is structurally impossible from this module alone —
callers (see backend/app/services/search_service.py) are responsible for
that filtering.
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.categorization.features import build_text_feature

MIN_SIMILARITY = 0.05


def search_transactions(transactions: pd.DataFrame, query: str, top_k: int = 10) -> list[dict]:
    """Rank `transactions` by semantic similarity to `query`.

    `transactions` must contain: transaction_id, merchant, description,
    category, amount, date. Returns an empty list if there are no
    transactions to search or the query has no meaningful overlap with
    any of them (never fabricates a "best guess" match).
    """
    if transactions.empty or not query.strip():
        return []

    corpus = build_text_feature(transactions["merchant"], transactions["description"])
    corpus = corpus.tolist() + [query]

    vectorizer = TfidfVectorizer(max_features=2000, ngram_range=(1, 2))
    try:
        matrix = vectorizer.fit_transform(corpus)
    except ValueError:
        # Empty vocabulary (e.g. every field was blank) — nothing to rank.
        return []

    query_vector = matrix[-1]
    transaction_vectors = matrix[:-1]
    similarities = cosine_similarity(query_vector, transaction_vectors)[0]

    working = transactions.reset_index(drop=True).copy()
    working["similarity"] = similarities
    working = working[working["similarity"] >= MIN_SIMILARITY].sort_values("similarity", ascending=False)

    results = []
    for _, row in working.head(top_k).iterrows():
        results.append(
            {
                "transaction_id": int(row["transaction_id"]),
                "merchant": row.get("merchant"),
                "description": row.get("description"),
                "category": row["category"],
                "amount": float(row["amount"]),
                "date": str(row["date"]),
                "similarity": round(float(row["similarity"]), 4),
            }
        )
    return results
