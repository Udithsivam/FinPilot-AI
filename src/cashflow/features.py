"""Monthly income/expense/cash-flow panel, mirroring
src/forecasting/features.py but tracking income alongside expense so it
can forecast net_cash_flow = income - expense."""

import pandas as pd

from src.categorization.taxonomy import top_level_categories

CATEGORY_COLUMNS = top_level_categories()

FEATURE_COLUMNS = [
    "monthly_income",
    "monthly_expense",
    "net_cash_flow",
    "transaction_count",
    "recurring_expense",
    "average_transaction",
    "savings_rate",
    "previous_month_income",
    "previous_month_expense",
    "previous_month_cash_flow",
    "rolling_income",
    "rolling_expense",
    "rolling_cash_flow",
] + [f"category_{c}" for c in CATEGORY_COLUMNS]

TARGET_INCOME = "next_month_income"
TARGET_EXPENSE = "next_month_expense"
TARGET_CASH_FLOW = "next_month_cash_flow"

REQUIRED_COLUMNS = ["user_id", "date", "amount", "transaction_type", "category", "is_recurring"]


def build_monthly_panel(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"build_monthly_panel: missing required columns: {missing}")

    working = df.copy()
    working["date"] = pd.to_datetime(working["date"])
    working["month"] = working["date"].dt.to_period("M")

    expense = working[working["transaction_type"] == "expense"].copy()
    income = working[working["transaction_type"] == "income"].copy()

    monthly = (
        expense.groupby(["user_id", "month"])
        .agg(
            monthly_expense=("amount", "sum"),
            transaction_count=("amount", "count"),
            average_transaction=("amount", "mean"),
        )
        .reset_index()
    )

    income_monthly = income.groupby(["user_id", "month"])["amount"].sum().rename("monthly_income").reset_index()
    monthly = monthly.merge(income_monthly, on=["user_id", "month"], how="outer")
    monthly["monthly_expense"] = monthly["monthly_expense"].fillna(0.0)
    monthly["monthly_income"] = monthly["monthly_income"].fillna(0.0)
    monthly["transaction_count"] = monthly["transaction_count"].fillna(0).astype(int)
    monthly["average_transaction"] = monthly["average_transaction"].fillna(0.0)

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
    for col in [f"category_{c}" for c in CATEGORY_COLUMNS]:
        monthly[col] = monthly[col].fillna(0.0)

    monthly = monthly.sort_values(["user_id", "month"]).reset_index(drop=True)

    monthly["net_cash_flow"] = monthly["monthly_income"] - monthly["monthly_expense"]
    monthly["savings_rate"] = monthly.apply(
        lambda r: (r["net_cash_flow"] / r["monthly_income"]) if r["monthly_income"] > 0 else 0.0, axis=1
    )

    grouped = monthly.groupby("user_id")
    monthly["previous_month_income"] = grouped["monthly_income"].shift(1)
    monthly["previous_month_expense"] = grouped["monthly_expense"].shift(1)
    monthly["previous_month_cash_flow"] = grouped["net_cash_flow"].shift(1)
    monthly["rolling_income"] = grouped["monthly_income"].transform(
        lambda s: s.rolling(window=2, min_periods=1).mean()
    )
    monthly["rolling_expense"] = grouped["monthly_expense"].transform(
        lambda s: s.rolling(window=2, min_periods=1).mean()
    )
    monthly["rolling_cash_flow"] = grouped["net_cash_flow"].transform(
        lambda s: s.rolling(window=2, min_periods=1).mean()
    )

    return monthly


def build_supervised_frame(monthly: pd.DataFrame) -> pd.DataFrame:
    frame = monthly.copy()
    frame[TARGET_INCOME] = frame.groupby("user_id")["monthly_income"].shift(-1)
    frame[TARGET_EXPENSE] = frame.groupby("user_id")["monthly_expense"].shift(-1)
    frame[TARGET_CASH_FLOW] = frame.groupby("user_id")["net_cash_flow"].shift(-1)
    frame["target_month"] = frame["month"] + 1
    frame = frame.dropna(
        subset=["previous_month_income", "previous_month_expense", TARGET_CASH_FLOW]
    ).reset_index(drop=True)
    return frame


def latest_feature_row(monthly: pd.DataFrame, user_id: int) -> pd.Series | None:
    user_rows = monthly[monthly["user_id"] == user_id].sort_values("month")
    if len(user_rows) < 2:
        return None
    return user_rows.iloc[-1]
