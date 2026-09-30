import pandas as pd

from src.search.semantic_search import search_transactions


def _txn(txn_id, merchant, description, category="Food", amount=500, date="2026-01-01"):
    return {
        "transaction_id": txn_id,
        "merchant": merchant,
        "description": description,
        "category": category,
        "amount": amount,
        "date": date,
    }


def test_search_finds_semantically_related_transactions():
    df = pd.DataFrame(
        [
            _txn(1, "Swiggy", "Swiggy Order food delivery"),
            _txn(2, "Zomato", "Zomato Order food delivery"),
            _txn(3, "Uber", "Uber ride", category="Transportation"),
            _txn(4, "Netflix", "Netflix Subscription", category="Subscriptions"),
        ]
    )
    results = search_transactions(df, "food delivery order", top_k=5)
    ids = [r["transaction_id"] for r in results]
    assert 1 in ids
    assert 2 in ids
    assert ids.index(1) < ids.index(4) if 4 in ids else True


def test_search_returns_empty_for_empty_corpus():
    df = pd.DataFrame(columns=["transaction_id", "merchant", "description", "category", "amount", "date"])
    assert search_transactions(df, "food") == []


def test_search_returns_empty_for_blank_query():
    df = pd.DataFrame([_txn(1, "Swiggy", "Swiggy Order")])
    assert search_transactions(df, "   ") == []


def test_search_excludes_unrelated_transactions():
    df = pd.DataFrame(
        [
            _txn(1, "Swiggy", "Swiggy food delivery order"),
            _txn(2, "LIC", "LIC Insurance Premium Payment", category="Insurance", amount=5000),
        ]
    )
    results = search_transactions(df, "food delivery")
    ids = [r["transaction_id"] for r in results]
    assert 1 in ids
    assert 2 not in ids
