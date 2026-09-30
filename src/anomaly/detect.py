"""User-specific transaction anomaly detection.

Two methods, combined:

1. A statistical baseline — each expense transaction is compared against
   *that user's own* mean/std for its category (z-score). This is what
   makes a reason like "3.2x your typical Transportation transaction"
   honest: it's a real ratio against the user's own historical average,
   not a fixed global threshold.
2. IsolationForest, fit per-user on a small feature vector (amount,
   category z-score, day-of-week, is_recurring), to catch multivariate
   anomalies a single-category z-score would miss (e.g. an unusual
   combination of category + timing that isn't extreme on amount alone).

A transaction needs at least MIN_HISTORY prior expense transactions in
the same category (statistical) or MIN_TRANSACTIONS total (Isolation
Forest) before it is evaluated at all — with too little history there is
no genuine "normal" to deviate from, and we report that honestly instead
of guessing.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

MIN_CATEGORY_HISTORY = 4
MIN_TRANSACTIONS_FOR_ISOLATION_FOREST = 15
Z_SCORE_WARNING = 2.0
Z_SCORE_CRITICAL = 3.0
RANDOM_STATE = 42


def _severity_from_zscore(z: float) -> str:
    if abs(z) >= Z_SCORE_CRITICAL:
        return "high"
    if abs(z) >= Z_SCORE_WARNING:
        return "medium"
    return "low"


def _statistical_flags(expense: pd.DataFrame) -> dict[int, dict]:
    """Per-transaction z-score against the user's own category mean/std,
    computed leave-one-out per category (the transaction being scored
    isn't included in its own baseline)."""
    flags: dict[int, dict] = {}
    for category, group in expense.groupby("category"):
        if len(group) < MIN_CATEGORY_HISTORY + 1:
            continue
        amounts = group["amount"].to_numpy()
        for idx, row in group.iterrows():
            other_amounts = np.delete(amounts, np.where(group.index.to_numpy() == idx)[0])
            if len(other_amounts) < MIN_CATEGORY_HISTORY:
                continue
            mean = other_amounts.mean()
            std = other_amounts.std()
            if std == 0:
                continue
            z = (row["amount"] - mean) / std
            if abs(z) >= Z_SCORE_WARNING:
                ratio = row["amount"] / mean if mean > 0 else float("inf")
                flags[row["transaction_id"]] = {
                    "method": "statistical_zscore",
                    "anomaly_score": round(float(abs(z)), 2),
                    "severity": _severity_from_zscore(z),
                    "reason": (
                        f"Amount is {ratio:.1f}x your typical {category} transaction "
                        f"(usual average: {mean:,.0f}, this transaction: {row['amount']:,.0f})."
                    ),
                    "expected_range": f"{max(mean - std, 0):,.0f}–{mean + std:,.0f}",
                }
    return flags


def _isolation_forest_flags(expense: pd.DataFrame) -> dict[int, dict]:
    if len(expense) < MIN_TRANSACTIONS_FOR_ISOLATION_FOREST:
        return {}

    working = expense.copy()
    working["date"] = pd.to_datetime(working["date"])
    working["day_of_week"] = working["date"].dt.dayofweek
    category_mean = working.groupby("category")["amount"].transform("mean")
    category_std = working.groupby("category")["amount"].transform("std").replace(0, np.nan)
    working["category_zscore"] = ((working["amount"] - category_mean) / category_std).fillna(0.0)

    features = working[["amount", "category_zscore", "day_of_week", "is_recurring"]].copy()
    features["is_recurring"] = features["is_recurring"].astype(int)

    model = IsolationForest(n_estimators=200, contamination="auto", random_state=RANDOM_STATE)
    model.fit(features)
    scores = model.decision_function(features)  # lower = more anomalous
    predictions = model.predict(features)  # -1 = anomaly, 1 = normal

    flags: dict[int, dict] = {}
    for (_, row), score, pred in zip(working.iterrows(), scores, predictions):
        if pred != -1:
            continue
        severity = "high" if score < -0.15 else "medium"
        flags[row["transaction_id"]] = {
            "method": "isolation_forest",
            "anomaly_score": round(float(-score), 3),
            "severity": severity,
            "reason": (
                f"This {row['category']} transaction's combination of amount, timing and "
                f"recurrence pattern is unusual compared with your overall transaction history."
            ),
            "expected_range": None,
        }
    return flags


def detect_anomalies(transactions: pd.DataFrame) -> list[dict]:
    """Detect anomalies among one user's own expense transactions.

    `transactions` must contain: transaction_id, date, amount,
    transaction_type, category, is_recurring, merchant. Returns a list of
    dicts sorted by anomaly_score descending; empty if there isn't enough
    history to evaluate anything (never fabricated).
    """
    expense = transactions[transactions["transaction_type"] == "expense"].reset_index(drop=True)
    if expense.empty:
        return []

    statistical = _statistical_flags(expense)
    isolation = _isolation_forest_flags(expense)

    merged: dict[int, dict] = dict(statistical)
    for txn_id, flag in isolation.items():
        if txn_id in merged:
            # Both methods flagged it — keep the higher-severity statistical
            # explanation (it's more interpretable) but note both agreed.
            merged[txn_id]["method"] = "statistical_zscore+isolation_forest"
        else:
            merged[txn_id] = flag

    lookup = expense.set_index("transaction_id")
    results = []
    for txn_id, flag in merged.items():
        row = lookup.loc[txn_id]
        results.append(
            {
                "transaction_id": int(txn_id),
                "merchant": row.get("merchant"),
                "amount": float(row["amount"]),
                "category": row["category"],
                "date": str(row["date"]),
                **flag,
            }
        )

    results.sort(key=lambda r: r["anomaly_score"], reverse=True)
    return results
