"""Text feature construction for transaction categorization.

Kept deliberately simple and reused identically at training and
inference time (src/categorization/train.py and predict.py both import
this), so there is no train/serve skew in how the text feature is built
— the same failure mode this project already guards against in the
savings-prediction pipeline (src/features/build_features.py).
"""

import pandas as pd


def build_text_feature(merchant: pd.Series | str, description: pd.Series | str):
    """Concatenate merchant + description into one text field for TF-IDF.

    Accepts either pandas Series (training, vectorized) or plain strings
    (a single inference call).
    """
    if isinstance(merchant, str):
        return f"{merchant or ''} {description or ''}".strip()
    merchant = merchant.fillna("")
    description = description.fillna("")
    return (merchant + " " + description).str.strip()
