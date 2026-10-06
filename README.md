# AI-Powered CRM Lead Prioritization & Next-Best-Action System

## Problem
CRM teams often possess large databases of leads and prospective clients but have severely limited sales capacity. The core challenge is prioritization: distinguishing high-value, highly-likely-to-convert leads from inactive or cold prospects, and knowing exactly what action to take next to maximize the chance of conversion.

## Solution
This project implements an intelligent, deterministic CRM system that:
* **Predicts conversion probability** using a trained Gradient Boosting classifier.
* **Converts probability into a lead score** (0-100 scale) for intuitive ranking.
* **Ranks leads** to optimize daily sales workflows.
* **Explains predictions using SHAP** (Shapley Additive exPlanations) to build trust and highlight key factors driving the score.
* **Recommends the Next-Best-Action** (`CALL`, `EMAIL`, `DEMO`, `NURTURE`, `REVIEW`) using a deterministic rule engine based on the ML probability and feature states.
* **Allows human override** to incorporate sales rep intuition and context without breaking the deterministic flow.
* **Stores feedback** explicitly into the database for future ground-truth offline training.
* **Monitors model and data drift** using Kolmogorov-Smirnov (KS) and Total Variation Distance (TVD) metrics.

## Architecture

```text
CRM Data
   ↓
Feature Engineering
   ↓
Rule-Based Baseline
   ↓
GradientBoosting ML Model
   ↓
Conversion Probability
   ↓
Lead Score
   ↓
SHAP Explanation
   ↓
Next-Best-Action Rule Engine
   ↓
Persistence (SQLModel / PostgreSQL)
   ↓
FastAPI Backend
   ↓
Next.js CRM Dashboard
   ↓
Human Accept / Override
   ↓
Feedback Storage
   ↓
Evaluation & Monitoring
```

## ML Pipeline
1. **Feature Engineering**: CRM interaction data is strictly time-bounded (no future leakage). Protected attributes (race, gender, etc.) are explicitly excluded from the model. 
2. **Rule-Based Baseline**: Before training any ML, a domain-driven heuristic baseline is established to provide a floor for performance comparison.
3. **GradientBoostingClassifier**: The champion model predicts binary conversion probability.
4. **SHAP TreeExplainer**: Calculates feature-level contribution to the specific prediction.
5. **Evaluation**: Offline pipeline evaluates precision, recall, F1, ROC-AUC, and calibration.
6. **Monitoring**: Evaluates prediction drift and performance degradation on production data against training distributions.

## Explainability
* **ML generates the probability**: The Gradient Boosting model is the sole decider of conversion likelihood.
* **SHAP explains the actual model**: Explanations are mathematically derived directly from the tree paths, not hallucinated.
* **Recommendation rules are deterministic**: A separate business rule engine translates the ML score into an action.
* **No LLM Hallucinations**: Large Language Models are intentionally *not* responsible for scores, predictions, or SHAP values.

## Human-in-the-Loop
The system treats ML recommendations as advisory.
* **Acceptance**: Sales reps can explicitly accept the recommendation.
* **Override**: Reps can select an alternative action and must provide a rationale.
* **Immutability**: The system securely records the human feedback while preserving the original ML recommendation to enable precise future audits.

## Monitoring
The system uses an out-of-band batch monitor (`run_monitoring_and_retraining.py`) that observes prediction distributions and outputs states:
* `NO_ACTION`: System is healthy.
* `INVESTIGATE`: Minor drift detected, human review suggested.
* `RETRAIN_RECOMMENDED`: Significant degradation or drift detected.

**Note:** The system explicitly does *not* automatically retrain or replace production models. `RETRAIN_RECOMMENDED` is a signal for the data science team's CI/CD pipeline.

## Evaluation
The project implements reproducible baseline-vs-ML evaluation comparing the Rule-Based Baseline against the Gradient Boosting Classifier across classification, ranking, and calibration metrics. 

> **Important Constraint**: The project implements reproducible baseline-vs-ML evaluation, but final numeric evaluation could not be executed in the current Windows environment because Windows Application Control blocks required pandas/numpy/scikit-learn native DLLs.

## Demo Workflow (Hackathon / Interview Guide)

### Demo 1 — Hot Lead
Show a lead with high intent (e.g. `demo_requested=1`), resulting in a high conversion probability, high lead score, positive SHAP factors emphasizing the demo request, and a `DEMO` recommended action.

### Demo 2 — Cold/Inactive Lead
Show a lead with no recent activity (`days_since_last_contact > 90`), resulting in a low score, negative SHAP factors (recency penalty), and a `NURTURE` recommendation.

### Demo 3 — High-Value Opportunity
Show a lead with massive `deal_value` and decent engagement escalating automatically to a `REVIEW` or priority action, according to deterministic business rules.

### Demo 4 — Human Override
1. View a system recommendation (e.g., `EMAIL`).
2. Click **Override**, select `CALL`, and provide a reason ("Client is old-fashioned").
3. Submit. The feedback is stored, but the original ML prediction remains preserved immutably.

### Demo 5 — Monitoring
Execute the monitoring script to observe the emission of a `NO_ACTION` or `RETRAIN_RECOMMENDED` state. Emphasize that these are monitoring states, not automatic deployment actions.

## Final Model Artifact Documentation
* **Model**: `GradientBoostingClassifier`
* **Important configuration**: `n_estimators=100`, `max_depth=4`, `learning_rate=0.1`, `random_state=42`
* **Artifact Location**: `backend/data/model.joblib`
* **Loading Mechanism**: Loaded via `joblib` into the `app.ml.model.MLModel` wrapper class which guarantees deterministic inference.
* **Feature Schema**: Fully defined and validated by Pydantic schemas in the FastAPI application.

## Configuration & Startup Documentation

### Backend Setup
1. Clone repository
2. Create virtual environment: `python -m venv .venv`
3. Activate virtual environment: `.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure environment variables (copy `.env.example` to `.env`)
6. Initialize database: `python backend/scripts/init_db.py`
7. Start FastAPI backend: `cd backend && uvicorn app.main:app --reload`

*Note: If `pandas`/`scikit-learn` fail to import on Enterprise Windows due to Application Control (DLL blocks), run the environment in WSL or a Docker container.*

### Frontend Setup
1. Navigate to frontend: `cd frontend`
2. Install dependencies: `npm install`
3. Start frontend: `npm run dev`

## Technical Limitations
1. **Evaluation Environment**: Windows Application Control blocks native pandas/numpy/scikit-learn DLL execution in the current host environment. Therefore, automated pytest execution is blocked, direct ML evaluation execution is blocked, and numeric baseline-vs-ML performance results cannot currently be verified dynamically.
2. **Temporal Validation**: Because the dataset lacks suitable lead-level timestamps (e.g., `created_at` or `conversion_date`), the candidate model uses the documented stratified random split rather than claiming true time-aware out-of-time (OOT) validation.
3. **SHAP Granularity**: One-hot encoded categorical features (e.g., `industry_Tech`, `industry_Finance`) are explained independently by SHAP rather than grouped into their original categorical feature parent (`industry`).
4. **Monitoring**: Monitoring currently operates on the available reference datasets and does not perform active real-time data ingestion for drift analysis.

## Portfolio Project Summary
* **Tech Stack**: Python, Pandas, Scikit-learn, Gradient Boosting, SHAP, FastAPI, SQLModel (SQLite/PostgreSQL), Next.js, TypeScript.
* **Key Achievements**: 
  * Architected an end-to-end CRM intelligence layer featuring decoupled ML prediction, SHAP explainability, and deterministic rule-based next-best-action recommendations.
  * Implemented robust human-in-the-loop overrides, strictly capturing ground-truth data without corrupting immutable historical predictions.
  * Engineered a stateless, thin FastAPI layer orchestrating complex ML inferences backed by robust Pydantic data contracts.
  * Designed out-of-band monitoring to identify data drift (KS/TVD) securely without risking unauthorized automatic retraining deployments.
