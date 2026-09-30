import pandas as pd

from src.cashflow.features import (
    FEATURE_COLUMNS,
    TARGET_CASH_FLOW,
    build_monthly_panel,
    build_supervised_frame,
    latest_feature_row,
)


def _txn(user_id, date, amount, category="Groceries", ttype="expense", recurring=False):
    return {
        "user_id": user_id,
        "date": date,
        "amount": amount,
        "transaction_type": ttype,
        "category": category,
        "is_recurring": recurring,
    }


def test_build_monthly_panel_computes_net_cash_flow():
    df = pd.DataFrame(
        [
            _txn(1, "2026-01-01", 50000, ttype="income"),
            _txn(1, "2026-01-05", 1000, category="Groceries"),
            _txn(1, "2026-01-20", 500, category="Food"),
            _txn(1, "2026-02-01", 55000, ttype="income"),
            _txn(1, "2026-02-05", 1200, category="Groceries"),
        ]
    )
    monthly = build_monthly_panel(df)
    jan = monthly[monthly["month"].astype(str) == "2026-01"].iloc[0]
    assert jan["monthly_income"] == 50000
    assert jan["monthly_expense"] == 1500
    assert jan["net_cash_flow"] == 48500
    assert round(jan["savings_rate"], 4) == round(48500 / 50000, 4)

    feb = monthly[monthly["month"].astype(str) == "2026-02"].iloc[0]
    assert feb["previous_month_income"] == 50000
    assert feb["previous_month_cash_flow"] == 48500


def test_build_supervised_frame_targets_present():
    df = pd.DataFrame(
        [
            _txn(1, "2026-01-01", 50000, ttype="income"),
            _txn(1, "2026-01-05", 1000),
            _txn(1, "2026-02-01", 52000, ttype="income"),
            _txn(1, "2026-02-05", 1100),
            _txn(1, "2026-03-01", 53000, ttype="income"),
            _txn(1, "2026-03-05", 1200),
        ]
    )
    monthly = build_monthly_panel(df)
    frame = build_supervised_frame(monthly)
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row[TARGET_CASH_FLOW] == 53000 - 1200
    for col in FEATURE_COLUMNS:
        assert col in frame.columns


def test_latest_feature_row_requires_two_months():
    df = pd.DataFrame([_txn(1, "2026-01-01", 50000, ttype="income")])
    monthly = build_monthly_panel(df)
    assert latest_feature_row(monthly, user_id=1) is None
