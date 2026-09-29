"""Feature engineering for the savings-prediction model.

Validated data is cross-sectional (one row per user, no timestamps), so
time-based features such as rolling averages or month-over-month trends
do not apply here. Instead, raw expense amounts are normalized into
income-relative ratios, which are more comparable across users of very
different income levels than the raw amounts alone.
"""

import pandas as pd

EXPENSE_CATEGORIES = [
    "Rent",
    "Loan_Repayment",
    "Insurance",
    "Groceries",
    "Transport",
    "Eating_Out",
    "Entertainment",
    "Utilities",
    "Healthcare",
    "Education",
    "Miscellaneous",
]


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with income-relative financial ratio features added."""
    df = df.copy()

    categories_present = [c for c in EXPENSE_CATEGORIES if c in df.columns]
    df["Total_Expenses"] = df[categories_present].sum(axis=1)
    df["Expense_to_Income_Ratio"] = df["Total_Expenses"] / df["Income"]
    df["Debt_to_Income_Ratio"] = df["Loan_Repayment"] / df["Income"]
    df["Housing_Cost_Ratio"] = df["Rent"] / df["Income"]

    for category in categories_present:
        df[f"{category}_to_Income_Ratio"] = df[category] / df["Income"]

    return df
