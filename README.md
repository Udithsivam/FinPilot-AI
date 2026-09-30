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

**Phase 5 — Intelligence (done):** Financial Health Score
(`GET /analytics/health-score`), rule-based Insights and Recommendations
(computed directly from a user's own transactions/budgets, not ML),
real transaction categorization (TF-IDF/embedding classifier benchmark),
expense and cash-flow forecasting, anomaly detection, semantic
transaction search, and prediction explainability. See "Intelligence &
ML" below for what's real vs. explicitly not built.

**Phase 7 — RAG + LLM assistant (done, with a documented limitation):**
a curated financial-knowledge base, TF-IDF retrieval, and a grounded
`POST /ai/chat` endpoint that combines retrieved knowledge with the
user's own data and real model outputs. No LLM API key is configured in
this environment, so the "LLM" step is an honest deterministic
extractive/template synthesizer, not a generative model — see "RAG &
Financial Assistant" below.

**Phase 8 — MLOps lifecycle (done):** MLflow model registry with an
explicit candidate → validated → production → archived lifecycle,
promotion/rollback, prediction-performance monitoring, feature-drift
detection (Kolmogorov-Smirnov), and a feedback-driven retraining script.
Admin-gated via the `ADMIN_EMAILS` environment variable (no schema
migration required). See "MLOps" below.

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
- **No LLM provider is configured.** `POST /ai/chat` retrieves real
  knowledge and real user data/predictions, but the "answer" is
  assembled by a deterministic template (`ExtractiveProvider`), not a
  generative model — see "RAG & Financial Assistant".
- **RAG/semantic search use TF-IDF, not sentence-transformer
  embeddings.** `sentence-transformers` pulls in a multi-GB `torch`
  dependency; for a ~50-chunk knowledge base and per-user transaction
  search at this scale, the retrieval-quality difference wouldn't be
  visible, so TF-IDF + cosine similarity (already available via
  scikit-learn) was used instead. Swapping in a real embedding model
  only requires changing `src/rag/retrieval.py` / `src/search/`.
- **`Feedback` has no direct foreign key to `Transaction`** (only to
  `Prediction`, which doesn't store the original merchant/description
  text). `scripts/retrain_from_feedback.py` works around this by using
  the corrected category name itself as a weak text signal, rather than
  the transaction's real text — a real, documented gap, not silently
  hidden.
- **No is_admin column on `User`.** Admin-gated endpoints
  (`/monitoring/*`, `/mlops/*`) check an `ADMIN_EMAILS` environment
  variable instead, to avoid an Alembic-style migration this project
  deliberately doesn't have.
- **No automatic outcome collection for prediction-performance
  monitoring.** `PATCH /predictions/{id}/actual` lets a user record a
  real later-known outcome, but nothing does this automatically (e.g.
  next month's real expense isn't known until that month closes) — with
  no actuals recorded, `/monitoring/performance` honestly reports
  `insufficient_data` rather than a fabricated metric.
- XGBoost was added and benchmarked for expense/cash-flow forecasting;
  LightGBM/CatBoost and sentence-transformers were evaluated and
  deliberately not added (see "Model selection" below) given the
  dataset's small size and this project's dependency-footprint goals.

## Project layout

```
data/raw/              data.csv (savings, original), finpilot_*.csv (SYNTHETIC transactions)
data/knowledge/        curated RAG knowledge-base documents (markdown + YAML frontmatter)
src/data/              data loading and validation
src/features/          feature engineering (savings prediction)
src/pipeline/          shared preprocessing, training, MLflow tracking, inference, explainability
src/training/          candidate model definitions and training loop
src/evaluation/        evaluation metrics
src/categorization/    transaction categorization (taxonomy, features, train, predict)
src/forecasting/       expense forecasting (features, train, predict)
src/cashflow/          cash-flow forecasting (features, train, predict)
src/anomaly/           anomaly detection (statistical + IsolationForest)
src/search/            semantic transaction search (TF-IDF)
src/rag/               knowledge base, retrieval, LLM provider abstraction, assistant, evaluation
src/monitoring/        prediction-performance and drift-detection logic
src/registry/          MLflow model-registry lifecycle (candidate/validated/production/archived)
scripts/               dataset generation, demo seeding, feedback-driven retraining
models/                trained model artifacts (DVC-tracked)
reports/               metrics reports per model + RAG retrieval evaluation
params.yaml            savings-prediction pipeline configuration
dvc.yaml / dvc.lock    DVC pipeline definition (5 stages)
backend/app/           FastAPI application (see Backend section below)
tests/unit/            unit tests for ML/NLP/monitoring/registry logic
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
dvc pull   # fetch data.csv and the model artifacts from the remote
dvc push   # publish newly generated artifacts to the remote
dvc repro  # rerun any stage whose inputs changed
```

Five stages, each independently reproducible:

```
train              savings prediction   (data/raw/data.csv)
categorize_train   categorization       (data/raw/finpilot_transactions.csv)
forecast_train     expense forecasting  (data/raw/finpilot_transactions.csv)
cashflow_train     cash-flow forecasting (data/raw/finpilot_transactions.csv)
```

To regenerate the synthetic transaction dataset itself (deterministic,
fixed seed — see "Synthetic transaction dataset" below):

```
python -m scripts.generate_transaction_data
```

To run the feedback-driven retraining pipeline for the categorizer
(pulls validated `category_correction` feedback, retrains, logs a new
MLflow **candidate** — never auto-promoted):

```
python -m scripts.retrain_from_feedback
```

To re-run the RAG retrieval evaluation (`reports/rag_retrieval_evaluation.json`):

```
python -m src.rag.evaluation
```

## Synthetic transaction dataset

`data/raw/finpilot_users.csv` and `data/raw/finpilot_transactions.csv`
are a **synthetic transaction dataset designed to reproduce realistic
personal-finance transaction patterns for development and ML
experimentation** — generated deterministically (`SEED=7`, 40 users, 8
months, ~6,905 transactions, `scripts/generate_transaction_data.py`),
with ~18% of descriptions deliberately generic/uninformative to mirror
real bank-statement ambiguity. This is **not real customer banking
data**, and it is a separate dataset from `data/raw/data.csv` (the
original savings-prediction dataset, 20,000 rows, unmodified, still the
sole source for `/predict/savings`).

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
| Training | **Implemented** | `src/pipeline/train.py`, `src/categorization/train.py`, `src/forecasting/train.py`, `src/cashflow/train.py`, all via `dvc repro` |
| Evaluation | **Implemented** | `reports/*_metrics.json` per model, candidates compared on a held-out validation/test split |
| Experiment tracking | **Implemented** | MLflow, one experiment per model family, nested runs per candidate |
| Model registry | **Implemented** | `src/registry/model_registry.py` — an explicit `candidate → validated → production → archived` lifecycle on top of MLflow's registry (tracked as an MLflow version tag, `lifecycle_stage`) |
| Registry-based serving | **Implemented, with a controlled fallback** | `load_production_model()` loads the MLflow-registered production version when one exists; otherwise it falls back to the local DVC-tracked `.pkl` and says so explicitly (`source: "local_fallback"` vs `"registry"`) — never silently one or the other |
| Model promotion | **Implemented** | `POST /mlops/models/{name}/versions/{version}/promote` (admin-only), enforces the lifecycle state machine — e.g. `archived → production` is rejected |
| Model rollback | **Implemented** | `POST /mlops/models/{name}/rollback` (admin-only) — restores a previously-archived version to production and archives the current one; no artifact is ever deleted |
| Prediction-performance monitoring | **Implemented, honestly limited** | `GET /monitoring/performance` (admin-only) computes real MAE/RMSE/R² from predictions with a recorded actual outcome (`PATCH /predictions/{id}/actual`); reports `insufficient_data` otherwise, never a fabricated number |
| Data drift detection | **Implemented** | `GET /monitoring/drift` (admin-only) — Kolmogorov-Smirnov test comparing the synthetic training distribution against real recorded transaction amounts |
| Feedback-driven retraining | **Implemented as a manual, explicit step** | `python -m scripts.retrain_from_feedback` curates validated `category_correction` feedback, retrains, logs a new MLflow **candidate** version — it never auto-promotes |
| MLOps dashboard | **Implemented** | `GET /mlops/summary` (admin-only) + the `/mlops` frontend page: registry state, performance, drift, feedback counts, RAG index stats |

In one sentence: the original savings-prediction serving gap — **"MLflow tracks and registers every run, but nothing at serving time reads from it"** — is now closed for all four trainable models via `src/registry/model_registry.py`, with an explicit, tested promotion/rollback lifecycle and a controlled, clearly-labeled local fallback.

## Intelligence & ML

| Capability | Status | Notes |
|---|---|---|
| Savings prediction | **Implemented** | `GradientBoostingRegressor`, unchanged from Phase 2/3. Test: MAE 611.70, RMSE 2218.59, R² 0.9319 |
| Transaction categorization | **Implemented** | TF-IDF features; benchmarked `LogisticRegression` vs `LinearSVC` (calibrated) — `LinearSVC_calibrated` selected on macro-F1 (0.8836 vs 0.8771). Returns a `needs_review` flag below a confidence threshold instead of a false-confidence guess |
| Expense forecasting | **Implemented** | Monthly panel per user; chronological train/val/test split; baseline (2-month moving average) vs `RandomForestRegressor`/`GradientBoostingRegressor`/`XGBRegressor`, selected on validation MAE. `RandomForestRegressor` won even with XGBoost benchmarked (test MAE 7514 vs. baseline 8053) |
| Cash-flow forecasting | **Implemented** | Same panel extended with income; two regressors (income, expense) trained separately, `net_cash_flow` derived from both so the three numbers are always internally consistent |
| Anomaly detection | **Implemented** | Statistical z-score against the user's own per-category history (interpretable: "3.2x your typical X") + `IsolationForest` for multivariate patterns a single z-score misses. User-specific — never a global threshold |
| Semantic transaction search | **Implemented** | TF-IDF + cosine similarity over one user's own transactions, rebuilt per request (no persistent index — see "Known limitations" for why not FAISS/embeddings) |
| Recommendations | **Implemented** | Rule-based (budget utilization, category spend change, recurring-expense share, savings-rate drop) — real thresholds, not an LLM guess |
| Explainability | **Implemented** | Savings prediction: real `feature_importances_` + directional heuristic (no SHAP — not installed, see `src/pipeline/explain.py`). Categorization: real `predict_proba` confidence + `needs_review`. Anomalies: a human-readable reason tied to a real ratio/score |

### Model selection

Every trainable model in this repo follows the same rule: **candidates are
compared on a validation metric, and the winner is whichever number is
actually best — never whichever algorithm sounds most advanced.**
`XGBoost` was installed and benchmarked for both forecasting tasks;
`RandomForestRegressor` still won expense forecasting even with XGBoost in
the running. `LightGBM`/`CatBoost` were not added: with ~240 training
rows for forecasting and 6,585 for categorization, an additional boosting
library was judged very unlikely to move the metric enough to justify a
third dependency, and this project's own instructions call for avoiding
unnecessary architecture. `sentence-transformers` (for embedding-based
categorization/RAG) was evaluated the same way and not adopted — see
"Known limitations".

## RAG & Financial Assistant

`POST /ai/chat` combines three genuinely separate sources, never letting
one pretend to be another (see `src/rag/assistant.py`):

1. **User facts** — the caller's own structured data (dashboard totals,
   top spending category, anomalies), fetched from the same services the
   rest of the app uses. Never another user's data.
2. **Model predictions** — real outputs of the trained models (expense/
   cash-flow forecast), fetched the same way the Predictions page does.
3. **General knowledge** — chunks retrieved from a curated knowledge base
   at `data/knowledge/` (14 documents covering budgeting, emergency
   funds, debt, credit utilization, savings, cash flow, goals, investing,
   risk, insurance, terminology, and subscriptions — each with `source`/
   `title`/`topic` metadata), retrieved via TF-IDF + cosine similarity
   (`src/rag/retrieval.py`) and returned with numbered citations.

The active `LLMProvider` (`src/rag/providers.py`) only *arranges* these
three already-computed inputs into prose — with no `ANTHROPIC_API_KEY` or
`OPENAI_API_KEY` configured in this environment, the active provider is
`ExtractiveProvider`, a deterministic template, not a generative model, so
there is nothing for it to hallucinate. Adding a real key later only
requires implementing one more `LLMProvider` subclass; every caller
depends on the interface, not a specific provider.

**Retrieval evaluation** (`python -m src.rag.evaluation`,
`reports/rag_retrieval_evaluation.json`): 12 hand-written questions with
an expected source document, measuring Hit@4 — the last run scored
**11/12 (91.7%)**. This measures retrieval only; there is no generated-
answer faithfulness score, since there is no generative model to score.

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
GET /analytics/health-score   (rule-based, explainable financial health score)
GET /analytics/insights       (rule-based: category spend changes, savings streaks)
GET /analytics/recommendations (rule-based, real thresholds)
GET /analytics/anomalies      (statistical z-score + IsolationForest, user-specific)

POST /predict/savings         (savings prediction + real feature-importance explanation)
GET  /predictions/history
GET  /predictions/expenses    (next-month expense forecast)
GET  /predictions/cash-flow   (next-month income/expense/net cash flow forecast)
PATCH /predictions/{id}/actual (record a real later-known outcome, for monitoring)

POST /transactions/categorize (TF-IDF/LinearSVC categorizer; confidence + needs_review)
GET  /transactions/search     (semantic search over the caller's own transactions)

POST /feedback                 (category corrections etc., ownership-validated)

POST /ai/chat                  (grounded assistant — see "RAG & Financial Assistant")

GET  /monitoring/performance   (admin-only: real MAE/RMSE/R² per model)
GET  /monitoring/drift         (admin-only: Kolmogorov-Smirnov drift check)

GET  /mlops/models/{name}/versions
POST /mlops/models/{name}/versions/{version}/promote  (admin-only)
POST /mlops/models/{name}/rollback                    (admin-only)
GET  /mlops/summary            (admin-only — powers the /mlops frontend page)

GET /health
GET /metrics                   (Prometheus format)
```

Admin-only endpoints are gated by the `ADMIN_EMAILS` environment
variable (comma-separated emails), checked server-side against the
authenticated user — see `backend/app/api/deps.py::get_current_admin`.

## Tests

```
python -m pytest tests/
```

`tests/unit/` covers the ML/NLP/monitoring/registry logic in isolation;
`tests/api/` exercises the FastAPI backend end-to-end (including
cross-user isolation on every new endpoint) against an isolated
in-memory/temp-file SQLite database (no real database needed to run
them). `tests/unit/test_model_registry.py` and
`test_retrain_from_feedback.py` register real throwaway MLflow model
versions per test for isolation, rather than mutating the shared
`mlflow.db` used for manual demonstration.

## Note on `Desired_Savings_Percentage`

This column is excluded from the feature set (see `params.yaml`): it is
essentially `Desired_Savings / Income * 100`, so using it as a feature
would leak the target into the model.
