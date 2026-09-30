"""Monthly aggregation + supervised-learning frame for expense forecasting.

Turns raw transaction rows into one row per (user_id, calendar month), then
attaches next-month total expense as the prediction target. Used both to
build the training panel (from the synthetic transaction dataset) and, at
inference time, to build the same features from a real user's own
transactions (see backend/app/services/forecast_service.py).
"""

import pandas as pd

from src.categorization.taxonomy import top_level_categories

CATEGORY_COLUMNS = top_level_categories()

FEATURE_COLUMNS = [
    "total_expense",
    "transaction_count",
    "average_transaction",
    "recurring_expense",
    "previous_month_expense",
    "rolling_avg_expense",
    "trend",
] + [f"category_{c}" for c in CATEGORY_COLUMNS]

TARGET_COLUMN = "next_month_expense"

REQUIRED_COLUMNS = ["user_id", "date", "amount", "transaction_type", "category", "is_recurring"]


def build_monthly_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw transaction rows into one row per (user_id, month).

    Expects columns: user_id, date, amount, transaction_type
    ("income"/"expense"), category, is_recurring (bool). Extra columns are
    ignored. Rows are expense-only for every aggregate except the panel
    index itself, since this pipeline forecasts expenses, not income.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"build_monthly_panel: missing required columns: {missing}")

    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working["month"] = working["date"].dt.to_period("M")

    expense = working[working["transaction_type"] == "expense"].copy()
    if expense.empty:
        return pd.DataFrame(columns=["user_id", "month", *FEATURE_COLUMNS])

    monthly = (
        expense.groupby(["user_id", "month"])
        .agg(
            total_expense=("amount", "sum"),
            transaction_count=("amount", "count"),
            average_transaction=("amount", "mean"),
        )
        .reset_index()
    )

    recurring = (
        expense[expense["is_recurring"].astype(bool)]
        .groupby(["user_id", "month"])["amount"]
        .sum()
        .rename("recurring_expense")
        .reset_index()
    )
    monthly = monthly.merge(recurring, on=["user_id", "month"], how="left")
    monthly["recurring_expense"] = monthly["recurring_expense"].fillna(0.0)

    category_pivot = expense.pivot_table(
        index=["user_id", "month"], columns="category", values="amount", aggfunc="sum"
    ).fillna(0.0)
    category_pivot = category_pivot.reindex(columns=CATEGORY_COLUMNS, fill_value=0.0)
    category_pivot.columns = [f"category_{c}" for c in category_pivot.columns]
    category_pivot = category_pivot.reset_index()

    monthly = monthly.merge(category_pivot, on=["user_id", "month"], how="left")
    monthly = monthly.sort_values(["user_id", "month"]).reset_index(drop=True)

    monthly["previous_month_expense"] = monthly.groupby("user_id")["total_expense"].shift(1)
    monthly["rolling_avg_expense"] = monthly.groupby("user_id")["total_expense"].transform(
        lambda s: s.rolling(window=2, min_periods=1).mean()
    )
    monthly["trend"] = monthly["total_expense"] - monthly["previous_month_expense"]

    return monthly


def build_supervised_frame(monthly: pd.DataFrame) -> pd.DataFrame:
    """Attach next-month total expense as the target.

    Drops the first calendar month per user (no `previous_month_expense`
    yet) and the last (no future month to supply the target) — both are
    genuinely missing information, not values worth imputing.
    """
    frame = monthly.copy()
    frame[TARGET_COLUMN] = frame.groupby("user_id")["total_expense"].shift(-1)
    frame["target_month"] = frame["month"] + 1
    frame = frame.dropna(subset=["previous_month_expense", TARGET_COLUMN]).reset_index(drop=True)
    return frame


def latest_feature_row(monthly: pd.DataFrame, user_id: int) -> pd.Series | None:
    """The most recent month's feature row for one user, used at inference
    time to forecast that user's *next* month. Returns None if the user has
    fewer than two months of history (there'd be no `previous_month_expense`)."""
    user_rows = monthly[monthly["user_id"] == user_id].sort_values("month")
    if len(user_rows) < 2:
        return None
    return user_rows.iloc[-1]
