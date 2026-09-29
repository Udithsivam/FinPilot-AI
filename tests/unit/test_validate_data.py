import pandas as pd
import pytest

from src.data.validate_data import DataValidationError, validate_data

VALID_ROW = {
    "Income": 50000.0,
    "Age": 30,
    "Occupation": "Professional",
    "City_Tier": "Tier_1",
}


def make_df(**overrides):
    row = {**VALID_ROW, **overrides}
    return pd.DataFrame([row])


def test_valid_data_passes_through():
    df = make_df()
    result = validate_data(df)
    assert len(result) == 1


def test_missing_values_raise():
    df = make_df(Income=None)
    with pytest.raises(DataValidationError, match="missing values"):
        validate_data(df)


def test_negative_amount_raises():
    df = make_df(Income=-100.0)
    with pytest.raises(DataValidationError, match="negative values"):
        validate_data(df)


def test_zero_income_raises():
    df = make_df(Income=0.0)
    with pytest.raises(DataValidationError, match="non-positive"):
        validate_data(df)


def test_implausible_age_raises():
    df = make_df(Age=150)
    with pytest.raises(DataValidationError, match="plausible range"):
        validate_data(df)


def test_unknown_category_raises():
    df = make_df(Occupation="Astronaut")
    with pytest.raises(DataValidationError, match="unexpected categories"):
        validate_data(df, known_categories={"Occupation": ["Student", "Professional"]})


def test_duplicates_are_dropped():
    df = pd.concat([make_df(), make_df()], ignore_index=True)
    result = validate_data(df)
    assert len(result) == 1
