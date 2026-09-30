import pandas as pd

from src.forecasting.features import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
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


def test_build_monthly_panel_aggregates_per_user_month():
    df = pd.DataFrame(
        [
            _txn(1, "2026-01-05", 1000, category="Groceries", recurring=True),
            _txn(1, "2026-01-20", 500, category="Food"),
            _txn(1, "2026-02-05", 1200, category="Groceries"),
            _txn(1, "2026-01-01", 50000, ttype="income"),
        ]
    )
    monthly = build_monthly_panel(df)

    assert len(monthly) == 2
    jan = monthly[monthly["month"].astype(str) == "2026-01"].iloc[0]
    assert jan["total_expense"] == 1500
    assert jan["transaction_count"] == 2
    assert jan["recurring_expense"] == 1000
    assert jan["category_Groceries"] == 1000
    assert jan["category_Food"] == 500

    feb = monthly[monthly["month"].astype(str) == "2026-02"].iloc[0]
    assert feb["previous_month_expense"] == 1500
    assert feb["trend"] == 1200 - 1500


def test_build_supervised_frame_drops_first_and_last_month():
    df = pd.DataFrame(
        [
            _txn(1, "2026-01-05", 1000),
            _txn(1, "2026-02-05", 1200),
            _txn(1, "2026-03-05", 1400),
        ]
    )
    monthly = build_monthly_panel(df)
    frame = build_supervised_frame(monthly)

    # Only February has both a previous month (Jan) and a next month (Mar).
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row[TARGET_COLUMN] == 1400
    for col in FEATURE_COLUMNS:
        assert col in frame.columns


def test_latest_feature_row_requires_two_months():
    df = pd.DataFrame([_txn(1, "2026-01-05", 1000)])
    monthly = build_monthly_panel(df)
    assert latest_feature_row(monthly, user_id=1) is None

    df2 = pd.DataFrame([_txn(1, "2026-01-05", 1000), _txn(1, "2026-02-05", 1200)])
    monthly2 = build_monthly_panel(df2)
    row = latest_feature_row(monthly2, user_id=1)
    assert row is not None
    assert str(row["month"]) == "2026-02"
