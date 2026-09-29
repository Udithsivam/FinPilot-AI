"""Raw data loading for the savings-prediction pipeline."""

from pathlib import Path

import pandas as pd


def load_raw_data(path: str | Path) -> pd.DataFrame:
    """Load the raw financial records CSV into a DataFrame."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    return pd.read_csv(path)
