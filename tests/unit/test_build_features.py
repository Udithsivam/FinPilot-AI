import pandas as pd

from src.features.build_features import add_engineered_features


def test_engineered_ratios_are_computed_relative_to_income():
    df = pd.DataFrame([{
        "Income": 1000.0,
        "Rent": 300.0,
        "Loan_Repayment": 100.0,
        "Insurance": 0.0,
        "Groceries": 0.0,
        "Transport": 0.0,
        "Eating_Out": 0.0,
        "Entertainment": 0.0,
        "Utilities": 0.0,
        "Healthcare": 0.0,
        "Education": 0.0,
        "Miscellaneous": 0.0,
    }])

    result = add_engineered_features(df)

    assert result.loc[0, "Total_Expenses"] == 400.0
    assert result.loc[0, "Expense_to_Income_Ratio"] == 0.4
    assert result.loc[0, "Debt_to_Income_Ratio"] == 0.1
    assert result.loc[0, "Housing_Cost_Ratio"] == 0.3
    assert result.loc[0, "Rent_to_Income_Ratio"] == 0.3


def test_original_columns_are_preserved():
    df = pd.DataFrame([{"Income": 1000.0, "Rent": 100.0, "Loan_Repayment": 0.0}])
    result = add_engineered_features(df)
    assert "Income" in result.columns
    assert "Rent" in result.columns
