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

**Phase 5 — Intelligence (paused):** started with the Financial
Health Score (`GET /analytics/health-score`) and rule-based Insights
(`GET /analytics/insights` — month-over-month category changes and
savings-rate streaks, computed directly from a user's own transactions,
no ML model). Remaining Phase 5 work (categorization, forecasting,
anomaly detection, recommendations, real explainability) is paused —
the AI Insights page shows these as clearly-labeled "Sample" previews,
not real output.

**Phase 6 — Frontend (done):** a React + TypeScript + Vite app
(`frontend/`) with the full design system, app shell (sidebar/header/
mobile nav), reusable UI/financial/AI component libraries, and all 11
pages built and wired to the real backend: Landing, Login, Register,
Onboarding, Dashboard, Transactions, Budgets, Goals, Analytics,
AI Insights (sample-only, clearly marked), Predictions, and Settings.
See `frontend/README.md`.

**Backend/ML integration audit (done):** a correctness, test-coverage,
model-lifecycle and security pass over Phase 2-5. Found and fixed real
bugs — a malformed budget period (`period="not-a-period"`) crashed
`GET /budgets` with an unhandled 500 because the schema never validated
its format; over-72-byte passwords crashed both registration and login
because bcrypt raises above that length; budgets/goals/transactions
accepted zero or negative amounts. Also added: CORS middleware (missing
entirely — would have blocked any deployment with the frontend on a
different origin), a startup warning if `SECRET_KEY` is left at its
default, per-IP rate limiting on `/auth/login` and `/auth/register`,
and in-process caching for the ML pipeline (previously re-read from
disk on every single `/predict/savings` call). 25 new tests. See
"Known limitations" below for what's flagged but not fixed.

**Pre-review stabilization pass (done):** fixed a live correctness bug
where budget-vs-transaction category matching was exact-string
(`"Groceries"` didn't match `"groceries"`), normalized it at query time
(case/whitespace-insensitive SQL comparison); added executable
cross-user data-isolation regression tests for transactions, budgets
and goals (the scoping code was already correct, now it's proven by a
test, not just inspection); added `model_type`/`model_version` to the
`/predict/savings` response (the artifact's own content hash — not an
MLflow-registry version, since nothing reads from the registry at
serving time yet, see MLOps section below); added a deterministic demo
data seed script (`scripts/seed_demo_data.py`). 71 tests total
(`python -m pytest -q`), all passing.

### Known limitations (flagged, not fixed)

- Password strength: only length is enforced (8-72 chars), no
  complexity requirement.
- Rate limiting is in-process and per-instance — fine for a single
  server, not for a horizontally-scaled deployment (would need
  Redis-backed limiting).
- No JWT revocation/blocklist — logout is client-side only; a leaked
  token remains valid until it expires (24h by default).
- The ML pipeline cache means a newly retrained model isn't picked up
  until the API process restarts or `clear_pipeline_cache()` is called
  — there's no automatic invalidation hook from the training/DVC side yet.

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

## MLOps: what's actually implemented vs. planned

To avoid overstating the pipeline's maturity, here's the lifecycle
described in the original project brief, marked honestly:

| Stage | Status | Detail |
|---|---|---|
| Data validation | **Implemented** | `src/data/validate_data.py`, run in the training pipeline |
| Preprocessing / feature engineering | **Implemented** | `src/features/`, shared identically between training and inference (`src/pipeline/predict.py` imports the same function) |
| Training | **Implemented** | `src/pipeline/train.py`, `dvc repro` |
| Evaluation | **Implemented** | `reports/training_metrics.json`, 4 candidate models compared by R² |
| Experiment tracking | **Implemented** | MLflow, `src/pipeline/tracking.py` |
| Model registry | **Demonstration-ready** | MLflow's registry is populated on every training run (`finpilot-savings-predictor`), but nothing at serving time reads from it — see next row |
| Deployment / serving | **Implemented, but file-based, not registry-based** | `backend/app/api/predictions.py` loads a fixed path (`models/savings_prediction_pipeline.pkl`, DVC-tracked) via `src/pipeline/predict.py`, cached in-process. The response's `model_version` is this file's own content hash, not an MLflow model-version number |
| Monitoring / drift detection | **Planned** | Not built |
| Feedback-driven retraining | **Planned** | Not built — there's no predictions table yet to retrain against |
| Controlled model promotion | **Planned** | Not built |

In one sentence: **MLflow tracks and registers every training run, but the API does not currently serve "whatever MLflow says is Production" — it serves whatever file is on disk, and that file happens to also be DVC-tracked and MLflow-registered.** Closing that gap (registry-backed serving) is real, scoped future work, not a lie to paper over — see the backend/ML integration audit findings for the reasoning.

## Demo data

```
# with the backend running (uvicorn backend.app.main:app)
python -m scripts.seed_demo_data
```

Registers/logs in a `demo@finpilot.ai` user (password `DemoPass123!`,
both printed by the script) via the real public API — no direct DB
writes — and seeds 3 months of clearly-synthetic transactions, 3
budgets and 2 goals via the same endpoints a real client uses.
Deterministic (fixed random seed); safe to re-run. See
`scripts/seed_demo_data.py` for exactly what it creates — nothing here
is real financial data, and no seed script should ever be pointed at a
production database.

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
GET  /users/me/profile
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
GET /analytics/insights     (rule-based: category spend changes, savings streaks)

POST /predict/savings       (uses the Phase 2/3 trained pipeline; response
                             includes model_type and model_version — the
                             deployed artifact's own content hash)

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
