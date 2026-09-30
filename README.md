# FinPilot AI

AI-powered personal financial intelligence, expense management and end-to-end MLOps platform.

## Current status

**Phase 1 — Foundation (done):** dataset analysis, EDA and a baseline model
comparison notebook (`notebooks/Review1_EDA_Model.ipynb`).

**Phase 2 — Production ML (done):** a production preprocessing and
training pipeline under `src/`, replacing ad-hoc notebook preprocessing
with a single pipeline shared by training and inference.

**Phase 3 — MLOps (done):** DVC for data/model versioning and MLflow for
experiment tracking and a model registry, wired into the same training
pipeline via `dvc.yaml`.

**Phase 4 — Backend (done):** a FastAPI + SQLAlchemy backend
(`backend/`) with auth, user profiles, transactions, budgets, goals,
analytics, and a savings-prediction endpoint backed by the Phase 2/3
pipeline. Defaults to SQLite locally; point `DATABASE_URL` at Postgres
for production.

**Phase 5 — Intelligence (in progress):** started with the Financial
Health Score (`GET /analytics/health-score`) — a rule-based, explainable
score built from the user's own transactions/budgets/goals. Remaining
Phase 5 work (categorization, forecasting, anomaly detection,
recommendations, explainability) is not built yet.

## Project layout

```
data/raw/            raw input data (DVC-tracked, see data/raw/data.csv.dvc)
src/data/            data loading and validation
src/features/        feature engineering
src/pipeline/         shared preprocessing, training, MLflow tracking and inference
src/training/         candidate model definitions and training loop
src/evaluation/       evaluation metrics
models/                trained model artifacts (DVC-tracked)
reports/               training metrics reports
params.yaml            pipeline configuration
dvc.yaml / dvc.lock    DVC pipeline definition
backend/app/           FastAPI application (see Backend section below)
tests/unit/            unit tests for data validation and feature engineering
tests/api/             API tests for the FastAPI backend
```

## Environment setup

```
pip install -r requirements.txt
```

## Running the training pipeline

Directly:

```
python -m src.pipeline.train
```

Or, to also get DVC's dependency-aware caching (skips retraining if
nothing tracked by the `train` stage changed):

```
dvc repro
```

Either way this loads `data/raw/data.csv`, validates it, engineers
features, trains several candidate regressors behind a shared
`ColumnTransformer`, selects the best one by R², and saves:

- `models/savings_prediction_pipeline.pkl` — the fitted preprocessing +
  model pipeline (a single artifact usable directly for inference;
  DVC-tracked, not committed to git — see `dvc.yaml`)
- `reports/training_metrics.json` — held-out metrics for every candidate
  (git-tracked, so `git diff`/`dvc metrics diff` show metric history)

It also logs every candidate model as an MLflow run (params, metrics,
model artifact) under the `finpilot-savings-prediction` experiment, and
registers the selected model as a new version of the
`finpilot-savings-predictor` registered model.

## Data and model versioning (DVC)

`data/raw/data.csv` and `models/savings_prediction_pipeline.pkl` are
tracked by DVC rather than git — git only holds their small `.dvc`
pointer files, so large/binary artifacts never bloat the git history.

This repo's DVC remote (`localstorage` in `.dvc/config`) points at a
local folder (`../finpilot-ai-dvc-storage`, outside the repo) as a
stand-in for a real remote (S3/GCS/Azure Blob) — swap the remote URL
for one of those in production.

```
dvc pull   # fetch data.csv and the model artifact from the remote
dvc push   # publish newly generated artifacts to the remote
dvc repro  # rerun the training stage if its inputs changed
```

## Experiment tracking and model registry (MLflow)

Tracking data lives in a local SQLite database (`mlflow.db`, gitignored)
so the model registry works without a separate tracking server. To
browse runs and registered model versions:

```
mlflow ui --backend-store-uri sqlite:///mlflow.db
```

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

## Backend (FastAPI)

```
uvicorn backend.app.main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive API docs. By
default it uses a local SQLite file (`backend/finpilot.db`, gitignored);
copy `.env.example` to `.env` and set `DATABASE_URL` to point at
Postgres instead for production.

Endpoints implemented so far:

```
POST /auth/register
POST /auth/login          (OAuth2 form: username=email, password)

GET  /users/me
PUT  /users/me/profile

POST   /transactions
GET    /transactions
DELETE /transactions/{id}

POST   /budgets
GET    /budgets            (includes spent/remaining/utilization/status)
DELETE /budgets/{id}

POST   /goals
GET    /goals               (includes progress percentage)
DELETE /goals/{id}

GET /analytics/dashboard
GET /analytics/monthly
GET /analytics/categories
GET /analytics/health-score  (rule-based, explainable financial health score)

POST /predict/savings       (uses the Phase 2/3 trained pipeline)

GET /health
GET /metrics                (Prometheus format)
```

Receipt OCR / bank statement import, AI categorization, recommendations
and feedback endpoints are Phase 5 (Intelligence) work and not built yet.

## Tests

```
python -m pytest tests/
```

`tests/unit/` covers the ML pipeline; `tests/api/` exercises the FastAPI
backend end-to-end against an isolated in-memory/temp-file SQLite
database (no real database needed to run them).

## Note on `Desired_Savings_Percentage`

This column is excluded from the feature set (see `params.yaml`): it is
essentially `Desired_Savings / Income * 100`, so using it as a feature
would leak the target into the model.
