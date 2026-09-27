# AI-Powered CRM Lead Prioritization & Next-Best-Action System

An explainable ML system that analyzes CRM lead data, predicts lead quality/conversion probability, ranks leads, recommends the next best sales action, explains recommendations via SHAP, provides pipeline analytics, and supports human overrides/feedback.

## Project Structure

```
crm-ai/
│
├── backend/
│   ├── app/
│   │   ├── api/          # API route definitions and endpoints
│   │   ├── models/       # Database SQLModel schemas
│   │   ├── schemas/      # Pydantic schemas / DTOs
│   │   ├── services/     # Business logic & recommendation engine
│   │   ├── ml/           # Feature engineering, ML models, SHAP explainers
│   │   ├── core/         # Config, database connections, security
│   │   └── main.py       # FastAPI application entrypoint
│   │
│   ├── data/             # CRM raw and processed datasets (ignored/versioned)
│   ├── tests/            # Pytest test suite
│   ├── requirements.txt  # Python backend dependencies
│   └── .env.example      # Example backend environment variables
│
├── frontend/             # Next.js, TypeScript, Tailwind CSS, shadcn/ui application
│
├── notebooks/            # Exploratory data analysis and model training experiments
│
├── docs/                 # Architectural specifications, API and ML documentation
│
├── .gitignore
└── README.md
```

## Quick Start (Environment Verification)

### Backend
1. Navigate to `backend`:
   ```bash
   cd backend
   python -m venv .venv
   .venv\Scripts\activate   # On Windows
   pip install -r requirements.txt
   ```
2. Verify FastAPI health check:
   ```bash
   uvicorn app.main:app --reload
   # GET http://127.0.0.1:8000/health -> {"status": "ok"}
   ```

### Frontend
1. Navigate to `frontend`:
   ```bash
   cd frontend
   npm run dev
   # Access http://localhost:3000
   ```

### Dataset Generation (Phase 2)
The project includes a synthetic dataset generator that outputs 3,000 lead records and associated daily behavioral interactions, alongside a validation script ensuring PRD data requirements.
1. Run data generation:
   ```bash
   cd backend
   python -m app.ml.data_generation
   ```
2. Run data validation tests:
   ```bash
   cd backend
   pytest tests/ml/test_data_validation.py
   ```
The dataset is saved to `backend/data/leads.csv` and `backend/data/interactions.csv`.

### Feature Engineering (Phase 3)
The project includes a feature engineering pipeline that transforms raw CRM data into a clean, model-ready feature dataset.
1. Run feature engineering:
   ```bash
   cd backend
   python -m app.ml.feature_engineering
   ```
2. Run feature engineering tests:
   ```bash
   cd backend
   pytest tests/ml/test_feature_engineering.py
   ```
The model-ready dataset is saved to `backend/data/model_ready_features.csv`.

### Baseline Model (Phase 4)
The project includes a transparent, rule-based baseline conversion predictor that establishes a measurable reference point for evaluating subsequent ML models.
1. Run baseline pipeline & evaluation:
   ```bash
   cd backend
   python -m app.ml.baseline
   ```
2. Run baseline tests:
   ```bash
   cd backend
   pytest tests/ml/test_baseline.py
   ```
The evaluation results are recorded in `backend/data/baseline_metrics.json`.
- **Methodology**: 80/20 train/test split with stratified target sampling (`random_state=42`).
- **Baseline Logic**: Heuristic domain rules based on intent signals (`demo_requested`, `pricing_page_visit`), engagement counts (`email_clicked`, `call_made`, `web_visit`), recency penalties (`days_since_last_contact`), and opportunity stages.
- **Measured Metrics (Test Set, N=600)**:
  - ROC-AUC: `0.750`
  - Precision: `0.594`
  - Recall: `0.640`
  - F1-Score: `0.616`
  - Top 10% Precision / Conversion Rate: `0.900` (Lift: `2.09x` vs 43.0% baseline)
  - Top 20% Precision / Conversion Rate: `0.808` (Lift: `1.88x` vs 43.0% baseline)

### ML Lead Scoring Model (Phase 5)
The project trains, evaluates, and persists candidate tabular ML models (Logistic Regression, Random Forest, Gradient Boosting) on the engineered feature dataset.
1. Run ML training and evaluation:
   ```bash
   cd backend
   python -m app.ml.train
   ```
2. Run ML model tests:
   ```bash
   cd backend
   pytest tests/ml/test_model.py
   ```
- **Champion Algorithm**: `GradientBoostingClassifier` (`n_estimators=100`, `max_depth=4`, `learning_rate=0.1`).
- **Scoring Definition**:
  - `Conversion Probability` = Model predicted class-1 probability $\in [0.0, 1.0]$.
  - `Lead Score` = `round(Conversion Probability * 100)` $\in [0, 100]$.
- **Artifacts**:
  - Model artifact: `backend/data/model.joblib`
  - Predictions: `backend/data/predictions.csv`
  - Metrics & Comparison: `backend/data/model_metrics.json`, `backend/data/model_comparison.json`
- **Measured Metrics (Test Set, N=600)**:
  - ROC-AUC: `0.773` (+0.023 over baseline)
  - Precision: `0.673` (+0.080 over baseline)
  - Recall: `0.543`
  - F1-Score: `0.601`
  - Brier Score: `0.192` (improved calibration vs baseline `0.208`)
  - Top 10% Precision / Conversion Rate: `0.900` (Lift: `2.09x`)
  - Top 20% Precision / Conversion Rate: `0.800` (Lift: `1.86x`)
  - Score Bucket 80–100 Conversion Rate: `85.33%` (64 / 75 leads)

### SHAP Explainability (Phase 6)
The project provides transparent feature-level explanations for individual leads using Tree SHAP, computes global feature importance, and generates natural-language rationales directly from SHAP contributors.
1. Run SHAP explainer & generate global importance:
   ```bash
   cd backend
   python -m app.ml.explain
   ```
2. Run SHAP explainability tests:
   ```bash
   cd backend
   pytest tests/ml/test_explain.py
   ```
- **Explainer Implementation**: `shap.TreeExplainer` applied to the persisted `GradientBoostingClassifier`.
- **Outputs**:
  - **Local Lead Explanation**: Ranked positive contributing factors, ranked negative contributing factors, top overall factors, and a natural-language rationale.
  - **Global Feature Importance**: Persisted in `backend/data/shap_global_importance.json`.
- **Top Global Drivers (Mean |SHAP|)**:
  1. `Demo Requested` (`0.9577`)
  2. `Website Duration (Seconds)` (`0.2103`)
  3. `Pricing Page Visits` (`0.1384`)
  4. `Opportunity Stage: New` (`0.1321`)
  5. `Opportunity Stage: Qualified` (`0.1266`)
  6. `Deal Value ($)` (`0.1175`)

### Next-Best-Action Engine (Phase 7)
The project evaluates deterministic score-band rules and CRM signals to recommend the optimal sales follow-up action with explicit confidence scores and traceable rationales.
1. Run Recommendation Engine tests:
   ```bash
   cd backend
   pytest tests/services/test_recommendation.py
   ```
- **Supported Actions**: `CALL`, `EMAIL`, `DEMO`, `NURTURE`, `REVIEW`.
- **Score-Band Rules**:
  - **$\ge 80$ (High Priority)**: `demo_requested > 0` $\to$ `DEMO`; otherwise $\to$ `CALL`.
  - **$60 - 79$ (Warm Opportunity)**: `high email engagement` $\to$ `EMAIL`; `strong recent interaction` $\to$ `CALL`.
  - **$40 - 59$ (Mid-Funnel)**: `NURTURE` (marketing nurturing workflow).
  - **$< 40$ (Cold Lead)**: `NURTURE` (automated long-term drip).
- **Separation of Concerns**:
  - `Conversion Probability`: ML model likelihood $\in [0.0, 1.0]$.
  - `Lead Score`: Integer prioritization index $\in [0, 100]$.
  - `Recommendation Confidence`: Separate deterministic rule-agreement certainty score $\in [0.50, 0.95]$ with explicit listed reasons.

### FastAPI Backend (Phase 8)
The project exposes ML predictive scoring, SHAP explainability, and Next-Best-Action recommendations through a clean, typed FastAPI communication layer.
1. Run local FastAPI backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8000
   ```
2. Run backend API tests:
   ```bash
   cd backend
   pytest tests/api/test_endpoints.py
   ```
3. OpenAPI Documentation:
   - Interactive Swagger UI: `http://localhost:8000/docs`
   - OpenAPI Schema: `http://localhost:8000/openapi.json`
- **Exposed Endpoints**:
  - `GET /health` — Liveness health check.
  - `POST /api/leads/score` — Returns conversion probability and 0–100 integer lead score.
  - `POST /api/leads/explain` — Returns Tree SHAP positive/negative contributing factors and rationale.
  - `POST /api/leads/recommend` — Returns Next-Best-Action recommendation, confidence, and rule trace.
  - `POST /api/leads/intelligence` — Combined unified intelligence payload (Scoring + SHAP + Recommendation).
  - `GET /api/leads/ranked` — Paginated list of prioritized CRM leads sorted descending by score.
  - `GET /api/leads/{lead_id}` — Complete intelligence for an existing lead by identifier.



### PostgreSQL & Human-in-the-Loop Feedback (Phase 9)
The project persists CRM leads and human-in-the-loop feedback into PostgreSQL, enabling future model evaluation without automatic, uncontrolled retraining.
1. Configure database via environment variables (e.g. in `.env`):
   ```
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/crm_db
   ```
2. Initialize database and seed with CRM leads:
   ```bash
   cd backend
   python scripts/init_db.py
   ```
3. Feedback Endpoints:
   - `POST /api/feedback/{lead_id}/accept` — Records that a salesperson accepted the Next-Best-Action recommendation.
   - `POST /api/feedback/{lead_id}/override` — Records that a salesperson selected a different action with a required free-text reason.
   - `GET /api/feedback` — Retrieves stored human feedback.
- **Constraints Maintained**: Submitting feedback records the interaction for analytics and evaluation, but does **NOT** automatically retrain the ML model.

### Next.js CRM Dashboard (Phase 10)
The project provides a Next.js front-end application tailored for sales representatives.
1. Run local Next.js frontend:
   ```bash
   cd frontend
   npm run dev
   ```
2. Run frontend tests:
   ```bash
   cd frontend
   npx vitest run
   ```
- **Features**:
  - **Overview**: Displays total leads, high-priority leads, average score, and pipeline value.
  - **Ranked Leads**: Sorts CRM leads by conversion probability, highlighting recommended actions.
  - **Lead Intelligence Panel**: Presents 0-100 scores, explicit recommendations, and Tree SHAP factor breakdowns.
  - **Human-in-the-Loop Feedback**: Empowers reps to formally *Accept* or *Override* ML recommendations natively from the UI.

### Evaluation, Model Monitoring & Performance Analysis (Phase 11)
The project encapsulates model evaluation securely within the backend architecture, explicitly divorcing analytical operations from UI logic or active inference pipelines.
1. Run full evaluation:
   ```bash
   cd backend
   python -m app.ml.evaluate
   ```
- **Evaluation Details**:
  - **Metrics**: Computes ROC-AUC, Precision, Recall, F1, Brier Score, and Confusion Matrix.
  - **Ranking & Top-K**: Computes Precision/Recall/Lift at top 10%, 20%, 30%.
  - **Calibration & Buckets**: Analyzes expected vs actual conversion rates across defined 0-100 score buckets and decile-based calibration curves.
  - **Artifacts**: Evaluation metrics are stored deterministically as JSON artifacts in `backend/data/evaluation_metrics.json` alongside existing artifacts `model_metrics.json` and `model_comparison.json`.

### Production Polish, End-to-End Validation & Hackathon Demo (Phase 12)
The project is structurally polished, thoroughly tested end-to-end (ML pipeline, database, API, and UI), and production-ready for hackathon demonstrations.

#### Hackathon Demo Flow:
1. **Initialize & Seed Database**: Run `python scripts/init_db.py` in the `backend` folder to configure PostgreSQL and seed CRM leads.
2. **Start Backend Engine**: Run `uvicorn app.main:app --reload` in the `backend` folder.
3. **Start Frontend Dashboard**: Run `npm run dev` or `npm run start` in the `frontend` folder.
4. **Dashboard View**: Navigate to `http://localhost:3000` to view the **CRM Overview Analytics** and the **Ranked Leads Table** driven by the backend ML pipeline.
5. **Inspect Intelligence**: Click any high-priority lead to open the **Lead Intelligence Panel**, showcasing its predicted conversion probability, score, deterministic recommendation, and real-time **SHAP explanation** graphs.
6. **Accept Recommendation**: Click "Accept" in the Intelligence Panel to simulate a sales rep adopting the system's Next-Best-Action, persisting feedback dynamically.
7. **Override Recommendation**: Choose another lead and click "Override". Select an alternative action and submit a custom rationale. The system validates the input and persists the human-in-the-loop override securely for future model training analysis.
