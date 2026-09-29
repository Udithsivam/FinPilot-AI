"""Validation checks applied before any preprocessing or training."""

import pandas as pd


class DataValidationError(ValueError):
    """Raised when incoming data fails validation checks."""


# Disposable_Income is a net figure (income minus expenses) and can
# legitimately be negative for overspending users, so it is deliberately
# excluded from this list.
NON_NEGATIVE_COLUMNS = [
    "Income",
    "Age",
    "Dependents",
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
    "Desired_Savings_Percentage",
    "Desired_Savings",
    "Potential_Savings_Groceries",
    "Potential_Savings_Transport",
    "Potential_Savings_Eating_Out",
    "Potential_Savings_Entertainment",
    "Potential_Savings_Utilities",
    "Potential_Savings_Healthcare",
    "Potential_Savings_Education",
    "Potential_Savings_Miscellaneous",
]


def validate_data(df: pd.DataFrame, known_categories: dict[str, list[str]] | None = None) -> pd.DataFrame:
    """Validate raw financial records and return a de-duplicated copy.

    Checks for missing values, negative amounts in columns that cannot be
    negative, implausible ages and unexpected categorical values. Raises
    DataValidationError listing every issue found rather than failing on
    the first one, so callers can fix the data in one pass.
    """
    issues = []

    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        issues.append(f"missing values found in columns: {missing.to_dict()}")

    for col in NON_NEGATIVE_COLUMNS:
        if col in df.columns and (df[col] < 0).any():
            issues.append(f"column '{col}' contains negative values")

    if "Age" in df.columns and ((df["Age"] < 0) | (df["Age"] > 120)).any():
        issues.append("column 'Age' contains values outside the plausible range 0-120")

    if "Income" in df.columns and (df["Income"] <= 0).any():
        issues.append("column 'Income' contains non-positive values")

    if known_categories:
        for col, allowed in known_categories.items():
            if col in df.columns:
                unexpected = set(df[col].unique()) - set(allowed)
                if unexpected:
                    issues.append(f"column '{col}' contains unexpected categories: {sorted(unexpected)}")

    if issues:
        details = "\n".join(f"- {issue}" for issue in issues)
        raise DataValidationError(f"Data validation failed:\n{details}")

    return df.drop_duplicates().reset_index(drop=True)
