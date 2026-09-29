# FinPilot AI

AI-powered personal financial intelligence, expense management and end-to-end MLOps platform.

## Current status

**Phase 1 — Foundation (done):** dataset analysis, EDA and a baseline model
comparison notebook (`notebooks/Review1_EDA_Model.ipynb`).

**Phase 2 — Production ML (in progress):** a production preprocessing and
training pipeline under `src/`, replacing ad-hoc notebook preprocessing
with a single pipeline shared by training and inference.

## Project layout

```
data/raw/            raw, versioned input data
src/data/            data loading and validation
src/features/        feature engineering
src/pipeline/         shared preprocessing, training and inference entrypoints
src/training/         candidate model definitions and training loop
src/evaluation/       evaluation metrics
models/                trained model artifacts
reports/               training metrics reports
tests/unit/            unit tests for data validation and feature engineering
params.yaml            pipeline configuration
```

## Running the training pipeline

```
python -m src.pipeline.train
```

This loads `data/raw/data.csv`, validates it, engineers features, trains
several candidate regressors behind a shared `ColumnTransformer`, selects
the best one by R², and saves:

- `models/savings_prediction_pipeline.pkl` — the fitted preprocessing +
  model pipeline (a single artifact usable directly for inference)
- `reports/training_metrics.json` — held-out metrics for every candidate

## Inference

```python
from src.pipeline.predict import predict_savings

predict_savings({
    "Income": 50000.0, "Age": 30, "Dependents": 1,
    "Occupation": "Professional", "City_Tier": "Tier_1",
    "Rent": 10000.0, "Loan_Repayment": 2000.0, ...
})
```

`predict_savings` applies the same feature engineering used during
training before calling the saved pipeline, so callers only need to
supply raw fields.

## Tests

```
python -m pytest tests/unit
```

## Note on `Desired_Savings_Percentage`

This column is excluded from the feature set (see `params.yaml`): it is
essentially `Desired_Savings / Income * 100`, so using it as a feature
would leak the target into the model.
