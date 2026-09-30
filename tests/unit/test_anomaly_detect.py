import pandas as pd

from src.anomaly.detect import detect_anomalies


def _txn(txn_id, date, amount, category="Groceries", ttype="expense", merchant="Store", recurring=False):
    return {
        "transaction_id": txn_id,
        "date": date,
        "amount": amount,
        "transaction_type": ttype,
        "category": category,
        "merchant": merchant,
        "is_recurring": recurring,
    }


def test_no_anomalies_with_insufficient_history():
    df = pd.DataFrame([_txn(1, "2026-01-01", 500), _txn(2, "2026-01-05", 520)])
    assert detect_anomalies(df) == []


def test_statistical_zscore_flags_outlier_amount():
    rows = [_txn(i, f"2026-01-{i:02d}", 500 + i, category="Groceries") for i in range(1, 8)]
    rows.append(_txn(99, "2026-01-20", 15000, category="Groceries"))
    df = pd.DataFrame(rows)

    results = detect_anomalies(df)
    flagged_ids = [r["transaction_id"] for r in results]
    assert 99 in flagged_ids
    flagged = next(r for r in results if r["transaction_id"] == 99)
    assert flagged["severity"] in ("medium", "high")
    assert "typical Groceries transaction" in flagged["reason"]
    assert flagged["expected_range"]


def test_normal_transactions_are_not_flagged():
    rows = [_txn(i, f"2026-01-{i:02d}", 500 + (i % 3) * 5, category="Groceries") for i in range(1, 10)]
    df = pd.DataFrame(rows)
    results = detect_anomalies(df)
    assert results == []


def test_anomalies_are_sorted_by_score_descending():
    rows = [_txn(i, f"2026-01-{i:02d}", 500, category="Groceries") for i in range(1, 8)]
    rows.append(_txn(50, "2026-01-20", 3000, category="Groceries"))
    rows.append(_txn(51, "2026-01-21", 8000, category="Groceries"))
    df = pd.DataFrame(rows)
    results = detect_anomalies(df)
    scores = [r["anomaly_score"] for r in results]
    assert scores == sorted(scores, reverse=True)


def test_income_transactions_are_ignored():
    df = pd.DataFrame(
        [_txn(i, f"2026-01-{i:02d}", 50000, ttype="income", category="Salary") for i in range(1, 8)]
    )
    assert detect_anomalies(df) == []
