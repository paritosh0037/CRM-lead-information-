# Architecture

## Project: AI-Powered CRM Lead Prioritization & Next-Best-Action System

---

## 1. System Philosophy

- The ML system is the real intelligence of the project — build it before the dashboard.
- Keep layers strictly separated: UI, API, business logic, ML logic, persistence.
- No unnecessary infrastructure. No Kafka, Kubernetes, Redis, or Celery unless a concrete requirement appears.
- SQLite is acceptable temporarily if PostgreSQL becomes a setup blocker — don't burn hackathon time fighting infra.

---

## 2. High-Level Architecture

```
                     USER / SALES REP
                            │
                            ▼
                 ┌────────────────────┐
                 │      Next.js       │
                 │     FRONTEND       │
                 │ Dashboard          │
                 │ Lead Ranking       │
                 │ Lead Details       │
                 │ Analytics          │
                 │ Recommendations    │
                 │ Override           │
                 └─────────┬──────────┘
                           │ HTTP / JSON
                           ▼
                 ┌────────────────────┐
                 │      FastAPI       │
                 │      API Layer     │
                 │ /leads             │
                 │ /scores            │
                 │ /recommendations   │
                 │ /analytics         │
                 │ /feedback          │
                 └─────────┬──────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
   │  ML ENGINE   │ │ PostgreSQL   │ │  Analytics   │
   │ Feature Eng. │ │ Leads        │ │  Services    │
   │ Prediction   │ │ Interactions │ │ Pipeline     │
   │ Scoring      │ │ Scores       │ │ Metrics      │
   │ SHAP         │ │ Recommends   │ │ Aggregation  │
   └──────┬───────┘ │ Overrides    │ └──────────────┘
          │          │ Feedback     │
          │          └──────────────┘
          ▼
   ┌────────────────────┐
   │ Recommendation      │
   │ Score: 87            │
   │ Action: DEMO          │
   │ Why: ...               │
   │ Confidence: ...         │
   └─────────┬────────────────┘
             ▼
          FastAPI → Next.js → Sales User → Accept/Override → Feedback Store
             → Model Evaluation / Improvement
```

---

## 3. ML Pipeline

```
CRM data → Feature engineering → ML model → Conversion probability
→ Lead score → SHAP explanation → Next-best-action rules → (optional) LLM phrasing layer
```

Rules:
- The LLM, if used at all, only rewords the SHAP-derived explanation into natural language. It never invents the score or the reasoning.
- Establish a rule-based baseline first; only then train and compare ML models.

### Candidate models
- Logistic Regression
- Random Forest
- Gradient Boosting

Evaluate on ROC-AUC, Precision, Recall, F1, Confusion Matrix, probability calibration, and ranking metrics. Do not assume a winner in advance — a simple interpretable model may win on defensibility even if not on raw accuracy.

### Feature engineering categories
1. Engagement features (e.g. `email_open_rate = emails_opened / emails_sent`, `click_rate`, `call_response_rate`)
2. Intent features (e.g. `pricing_page_visits`, `demo_requested`)
3. Recency features (e.g. `days_since_last_contact`)
4. Opportunity features (e.g. `opportunity_stage`, `deal_value`)
5. Account/profile features (e.g. `company_size`, `industry`, `annual_revenue`)
6. Interaction-history features

**Leakage rule:** never use information that would only be known after the prediction point.

---

## 4. Backend Architecture (FastAPI)

### Stack
Python 3.12 · pandas · numpy · scikit-learn · shap · joblib · fastapi · uvicorn · pydantic · sqlmodel · psycopg[binary] · python-dotenv · pytest · httpx

### Directory structure
```
backend/
├── app/
│   ├── api/
│   │   ├── leads.py
│   │   ├── recommendations.py
│   │   ├── analytics.py
│   │   └── feedback.py
│   │
│   ├── models/
│   │   ├── lead.py
│   │   ├── interaction.py
│   │   ├── prediction.py
│   │   ├── recommendation.py
│   │   └── feedback.py
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── lead_service.py
│   │   ├── scoring_service.py
│   │   ├── recommendation_service.py
│   │   ├── analytics_service.py
│   │   └── feedback_service.py
│   │
│   ├── ml/
│   │   ├── preprocessing.py
│   │   ├── feature_engineering.py
│   │   ├── train.py
│   │   ├── evaluate.py
│   │   ├── scoring.py
│   │   ├── explain.py
│   │   └── model.joblib
│   │
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   │
│   └── main.py
│
├── data/
├── tests/
├── requirements.txt
└── .env.example
```

**Layering rule:** API routes stay thin. Business logic lives in `services/`. ML logic lives in `ml/`. Database models live in `models/`.

### API endpoints (v1)

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/api/leads` | List leads |
| GET | `/api/leads/{lead_id}` | Single lead detail |
| GET | `/api/leads/ranked` | Leads ranked by score |
| GET | `/api/leads/{lead_id}/explanation` | SHAP explanation |
| GET | `/api/leads/{lead_id}/recommendation` | Recommended action + confidence |
| GET | `/api/analytics` | Aggregate pipeline analytics |
| POST | `/api/recommendations/{lead_id}/override` | Record an override |
| POST | `/api/feedback` | Record feedback |

Future: `POST /api/scoring/batch`, `POST /api/data/upload`, `GET /api/models/metrics`, `GET /api/pipeline/summary`.

### Example response — `GET /api/leads/{lead_id}`
```json
{
  "lead_id": "L1008",
  "score": 87,
  "conversion_probability": 0.87,
  "recommended_action": "schedule_demo",
  "recommendation_confidence": 0.91,
  "top_factors": [
    { "feature": "demo_requested", "impact": 0.22 },
    { "feature": "pricing_page_visits", "impact": 0.13 }
  ]
}
```

---

## 5. Database (PostgreSQL)

**Tables:** `leads`, `interactions`, `predictions`, `recommendations`, `overrides`, `feedback`

```
Lead
 ├── Interactions
 ├── Predictions
 ├── Recommendations
 ├── Overrides
 └── Feedback
```

SQLite is an acceptable temporary substitute; migrate to PostgreSQL once core logic is stable.

---

## 6. Frontend Architecture (Next.js)

### Stack
Next.js (App Router) · TypeScript · Tailwind CSS · shadcn/ui · Recharts · Lucide React · TanStack Query

### Directory structure
```
frontend/
├── app/
│   ├── dashboard/
│   ├── leads/
│   │   └── [id]/
│   ├── analytics/
│   └── layout.tsx
│
├── components/
│   ├── dashboard/
│   ├── leads/
│   ├── charts/
│   ├── recommendations/
│   └── ui/
│
├── lib/
│   ├── api.ts
│   └── types.ts
│
└── hooks/
```

**Boundary rule:** the frontend displays data, calls FastAPI, and visualizes analytics. No ML logic ever lives in the frontend.

### Core pages
1. Dashboard — totals, priority leads, pipeline value, average score, score distribution, conversion funnel, recommended actions
2. Ranked Leads — rank, company, score, opportunity stage, recommended action, trend
3. Lead Detail — score, conversion probability, recommendation, confidence, SHAP explanation, interaction timeline, accept/override controls
4. Analytics — score distribution, conversion rate, pipeline value, lead sources, score by stage, action distribution, high-risk/high-value segments

---

## 7. Data Flow Summary

```
User/CRM Data → Data Quality → Feature Engineering → ML Prediction → Lead Score
→ Explainability → Next-Best-Action → Recommendation → Salesperson
→ Accept/Override → Feedback → Evaluation → Future Improvement
```

---

## 8. Hardware / Environment Constraints

- Dev machine: Dell Inspiron 3593, 12 GB RAM, Python 3.12, no GPU
- Sufficient for: pandas, NumPy, scikit-learn, SHAP, FastAPI, PostgreSQL, Next.js, and 2K–50K+ tabular records depending on complexity
- Avoid: local LLM training, large neural networks, unnecessary distributed infrastructure, millions of synthetic records unless specifically required

---

## 9. Deployment (target, not urgent)

- Frontend: Vercel
- Backend: Render / Railway / another suitable Python host
- Database: managed PostgreSQL

Do not optimize deployment before the local system fully works end to end.

---

## 10. Feature & Data Contract (Phase 2)

This section establishes the canonical data contract for the ML system.

### Prediction Point
The system makes a prediction at a specific timestamp `T`. 
Only information known at or before `T` (e.g., `interaction.timestamp <= T`) is permitted to generate features. All future information is strictly excluded to prevent target leakage.

### Target Definition
The eventual outcome predicted by the model is the **`converted`** boolean flag (1 for converted/won, 0 for lost/open).

### Feature Engineering Flow
`CRM Data` → `Validation` → `Historical Filtering (by T)` → `Feature Engineering` → `Approved Feature Matrix` → `Model Input`

### Approved Features (Feature Registry)
- **Numeric:** `annual_revenue`, `budget`, `deal_value`, `previous_purchase`, `days_since_last_contact`
- **Categorical (One-Hot Encoded):** `industry`, `company_size`, `lead_source`, `opportunity_stage` (excluding post-conversion stages)
- **Behavioral (Aggregated <= T):** `email_opened`, `email_clicked`, `call_made`, `web_visit`, `pricing_page_visit`, `demo_requested`, `total_web_duration`, `total_interactions`

### Excluded Features & Leakage Prevention
- **Target Leakage:** `converted`, `closed_date`, `won_reason`, `lost_reason` are explicitly dropped.
- **Post-Outcome Data:** `opportunity_stage` values of "Closed Won", "Closed Lost", and "Closed" are mapped to "Unknown" prior to encoding.
- **Protected Attributes:** `race`, `religion`, `ethnicity`, `caste`, `gender` are strictly excluded from the feature matrix.

### Invalid & Missing Data Rules
- **Negative Values:** `budget`, `annual_revenue`, and `deal_value` cannot be negative. If negative, they are coerced to `0.0`.
- **Negative Timedeltas:** `days_since_last_contact` cannot be negative; invalid values are set to `NaN`.
- **Missing Financials:** Missing `budget`, `annual_revenue`, `deal_value`, and `previous_purchase` default to `0.0` (assuming no known value).
- **Missing History:** Missing `days_since_last_contact` defaults to `999.0` (indicating stale/unknown contact).
- **Missing Behavioral Events:** Missing interaction types explicitly mean `0` occurrences.
- **Missing Categories:** Missing categorical fields default to `"Unknown"`.

---

## 11. Baseline Scoring System (Phase 3)

### Purpose
Provides a transparent, deterministic heuristic score (0-100) and ranking to serve as a reference point for future ML models. It proves that the data pipeline works and provides immediate business value.

### Inputs
Consumes only Phase 2 approved features. Explicitly excludes protected attributes, future interactions, and target variables (leakage).

### Scoring Logic
Uses domain-driven additive weights starting from a base conversion probability of 15% (0.15).

### Weights
- **Intent**: `demo_requested` (+0.25), `pricing_page_visit` (+0.10)
- **Engagement**: `email_clicked` (+0.03 up to 5), `call_made` (+0.02 up to 5), `web_visit` (+0.01 up to 10)
- **Recency**: penalty for `days_since_last_contact` (-0.05 if >30 days, -0.10 if >90 days)
- **Opportunity**: `previous_purchase` (+0.05), `opportunity_stage` (Qualified +0.05, Proposal +0.08)
- **Financial (Bucketed)**: `deal_value` (>100k: +0.10, >10k: +0.05), `annual_revenue` (>1m: +0.05)

### Score Range
Outputs a continuous predicted probability `[0.01, 0.99]`, which maps to a final integer lead score exactly in the range **0–100**.

### Score Bands
Preserves Phase 1 bands: 80–100 (High), 60–79 (Medium-High), 40–59 (Medium), 0–39 (Low).

### Ranking
Given equal scores, deterministic tie-breaking is applied:
1. Score (Descending)
2. `deal_value` (Descending, if present)
3. `lead_id` (Ascending alphanumeric)

### Evaluation
Evaluates against the true `converted` flag using: ROC-AUC, Precision, Recall, F1, Brier Score, Precision@K, Lift, Top-K Conversion Rate, and Calibration Curves. Results are saved in `baseline_metrics.json`.

### Limitations
The baseline prediction (`predict_proba`) is an additive heuristic and is NOT a statistically calibrated probability. While it falls between 0 and 1, it may not perfectly match the true underlying probability distribution of lead conversion.

---

## 12. Candidate ML Model (Phase 4)

### Model
`GradientBoostingClassifier`

### Target
`converted` (Binary Classification: 1 = converted/won, 0 = lost/open)

### Features
Strictly consumes the output of the Phase 2 Feature Contract.

### Split
**Limitation Documented:** The available dataset (`model_ready_features.csv` / `leads.csv`) does not contain sufficient lead-level temporal milestones (`created_at` or `conversion_date`) to implement a robust out-of-time (OOT) validation split. 
To prevent silently defaulting to random splitting without acknowledgment, we explicitly document this limitation and fall back to a stratified random train/test split.

### Preprocessing
Numeric and categorical features are processed according to the Phase 2 contract rules. Missing values are filled with defaults and target leakage fields are aggressively stripped. The model is trained exclusively on the `X_train` split.

### Hyperparameters
- `n_estimators`: 100
- `max_depth`: 4
- `learning_rate`: 0.1
- `random_state`: 42

### Evaluation
The model is evaluated using the following metrics:
- ROC-AUC, Precision, Recall, F1, Brier Score
- Precision@K, Lift, Top-K Conversion Rate

### Baseline Comparison
The Phase 4 `GradientBoostingClassifier` is evaluated alongside the Phase 3 `RuleBasedBaseline` on the exact same test dataset split, with metrics directly compared in `model_vs_baseline_comparison.json`. 

### Model Artifact
The model is persisted using `joblib` at `data/model.joblib`. 
It is structured to contain both the trained model object AND structured metadata (e.g. `model_name`, `feature_names`, `hyperparameters`, `metrics`). An independent `model_metadata.json` is also exported. Inference is handled by the `MLModel` class in `app.ml.model`, guaranteeing determinism.

### Limitations
- **Temporal Splitting:** Lacking timestamps, we cannot guarantee the model won't exhibit drift if deployed into the future.
- **Calibration:** Brier score is measured but active calibration (like Platt scaling/Isotonic Regression) is not yet applied. Depending on results, the output probabilities may need adjustment before business use.

---

## 13. SHAP Explainability (Phase 5)

### Model Explained
The persisted Phase 4 `GradientBoostingClassifier` located at `data/model.joblib`. 

### Explainer
`shap.TreeExplainer` is used because it calculates exact SHAP values for tree-based machine learning models extremely efficiently. By default, it operates in the `model_output="raw"` mode, meaning SHAP values sum up to the model's log-odds (margin) rather than raw probabilities.

### Feature Alignment
Because `MLModel` is solely responsible for both predicting and explaining, it applies the exact same `_prepare_features` sequence during inference and explanation. SHAP directly correlates to the one-hot encoded or transformed column names (e.g., `industry_Technology`, `company_size_1000+`) enforced by the Phase 2 Feature Contract.

### Local Explanation
We expose `MLModel.explain(features)` to strictly return a local explanation for a single lead. 
The pipeline avoids expensive global SHAP calculations at inference time.

### Contribution Semantics
- **Base Value**: The expected value of the model output (in log-odds) over the training dataset.
- **Positive Factors**: Features that drove the prediction log-odds upward (towards conversion).
- **Negative Factors**: Features that drove the prediction log-odds downward (away from conversion).
Factors are always ranked internally by `abs(shap_value)` descending.

### Validation
We mathematically validate that `base_value + sum(shap_values) == margin_prediction` within a narrow numerical tolerance. We further validate that `expit(margin_prediction) == prediction_probability` (the sigmoid function of the margin equals the output of `predict_proba`).

### Human-readable Explanation
A deterministic string formatter translates the structured JSON factors into text (e.g., *"The prediction is increased by demo_requested (value: 1.0)"*). It deliberately picks the top 2 overall driving factors by magnitude. No LLM is used in this process to prevent hallucination.

### Limitations
- **Categorical Feature Aggregation:** One-hot encoded SHAP values are not currently summed back into their parent feature groups (e.g., `industry_X` + `industry_Y` -> `industry` total effect). They remain independent.
- **Probability Space:** Because `TreeExplainer` raw output is in log-odds, adding SHAP values directly does not yield a linear probability change (due to the sigmoid curve). The raw SHAP values define the contribution magnitude and direction in log-odds space.

---

## 14. Model + Recommendation Integration (Phase 6)

### End-to-End Flow
The pipeline has been integrated into a single deterministic flow orchestrated by `LeadService`:
`CRM Lead → DB Read → Feature Engineering → MLModel (Predict + Explain) → Recommendation Engine → DB Trace Persistence → API Response`

### Component Responsibilities
- **Feature Engineering**: Validates data, enforces the Phase 2 contract, strips targets/leakage.
- **MLModel**: Predicts binary `conversion_probability` and computes SHAP factors exclusively.
- **Lead Score**: Scales probability to a 0-100 integer.
- **Recommendation Engine**: Evaluates Phase 1 business rules based on the lead score and input features to select the next-best action (`CALL`, `DEMO`, etc.) and sets a deterministic `recommendation_confidence`.

### Important Separation
- **ML predicts.** (ML output dictates likelihood to convert, not what to do.)
- **SHAP explains.** (SHAP provides mathematical evidence for the prediction, not business logic.)
- **Rules recommend.** (Business rules independently dictate the next action based on the ML's probability score.)
- Human users remain able to override later (Phase 7+).

### Unified Result
The service layer returns a strictly typed `CombinedLeadIntelligenceResponse` grouping the prediction, explanation, and recommendation under a single cohesive object mapped to the initial `lead_id`. 

### Model Versioning and Persistence
Every generated decision is immediately persisted into the SQL database (`predictions` and `recommendations` tables). The prediction is firmly attached to the model's metadata (`model_version`), enabling future drift monitoring and debug traceability.
 
### API Boundary
The `LeadService` orchestrates the entire intelligence flow. The FastAPI endpoints simply validate requests and call `LeadService`, keeping the API layer completely devoid of ML, scoring, and recommendation rule logic.

---

## 15. Human-in-the-Loop (Phase 7)

### Core Principle
The recommendation is strictly advisory. The sales user must be able to **Accept** or **Override** the recommendation at any time. High model confidence does not prevent a human override.

### Accept Flow
When a user accepts a recommendation, a new `Feedback` record is created storing the `original_action` and an `actor_context` (e.g., user identity, though currently unauthenticated). The original recommendation remains untouched.

### Override Flow
When a user overrides a recommendation, they supply a `new_action` and a required free-text `reason`. A `Feedback` record is persisted containing the `original_action`, the `override_action`, the reason, and the `actor_context`.

### Immutability
The original `Recommendation` generated by the rule engine is completely immutable. It is never overwritten by an override. This preserves the exact state of the system at the time of the prediction, which is critical for future evaluation and auditing. Both the original recommendation and the human feedback exist in the database side-by-side.

### Feedback Storage
The `Feedback` model captures:
- `lead_id`
- `original_action`
- `override_action` (if overridden)
- `reason` (if overridden)
- `actor_context` (identity of the actor, if available)
- `timestamp`

### Actor Context
The system captures the `actor_context` passed through the API. Since the application currently lacks an authenticated identity provider, this is an arbitrary string provided by the client, representing a limitation of the current authentication infrastructure.

### No Automatic Retraining
Feedback strictly serves as data capture. Submitting feedback **DOES NOT** trigger model retraining, update model weights, modify model artifacts, or change recommendation thresholds. The `model.joblib` artifact remains completely unchanged. 

### Future Training
The accumulated feedback stored in the database represents a highly valuable dataset for ground-truth proxy labels (e.g., "What did the human actually do?"). This data may be consumed by an explicit future pipeline to train, evaluate, or fine-tune subsequent model versions. It is fundamentally an offline, scheduled process, not a real-time reactive one.

---

## 16. Evaluation, Monitoring & Retraining Safety (Phase 8-11)

### Monitoring
Monitoring operates on an out-of-band batch script (`run_monitoring_and_retraining.py`) designed to evaluate predictions in the `predictions` table against subsequent outcomes. It compares the evaluation population with the training baseline using metrics such as Kolmogorov-Smirnov (KS) and Total Variation Distance (TVD).

### Retraining Safety State Machine
The system calculates performance degradation and drift and outputs a deterministic state:
- `NO_ACTION`
- `INVESTIGATE`
- `RETRAIN_RECOMMENDED`

**Crucial Constraint:** `RETRAIN_RECOMMENDED` is merely a signal. The system **never** silently retrains, replaces `model.joblib`, or alters model versioning autonomously. Retraining remains a deliberate, human-supervised CI/CD pipeline step.

### Testing Limitations (Windows Application Control)
Automated evaluations (e.g., executing `evaluate_baseline_vs_ml.py` or running E2E `pytest` suites) are fundamentally restricted by local enterprise DLL policies (Windows Application Control). These policies block the loading of `pandas` and `scikit-learn` native C-extensions. Consequently:
- Local tests exhibit **DLL/import failures**.
- `PYTHONPATH/module resolution failures` may also appear due to script execution paths.
Validation is thus guaranteed through semantic trace analysis, strict deterministic code structuring, and static architecture compliance.
