# Tasks & Progress

## Project: AI-Powered CRM Lead Prioritization & Next-Best-Action System

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

Build order matters — do not skip ahead to the UI before the ML foundation (Phases 2–9) is real and evaluated.

---

## Phase 1 — Project Setup & Environment
- [x] Initialize `backend/` (Python 3.12 venv, `requirements.txt`)
- [x] Initialize `frontend/` (Next.js App Router, TypeScript, Tailwind, shadcn/ui)
- [x] Set up Git repo + branching convention
- [x] Create `.env.example` for backend config
- [x] Confirm local PostgreSQL (or SQLite fallback) runs

## Phase 2 — Synthetic CRM Dataset
- [x] Define full field schema (account, engagement, intent, recency, opportunity, history, label)
- [x] Generate 2,000–5,000 realistic lead records
- [x] Build realistic day-by-day interaction sequences (not random rows)
- [x] Confirm no protected/sensitive attributes are present anywhere in the schema
- [x] Save raw dataset under `backend/data/`

## Phase 3 — Data Validation & Cleaning
- [x] Schema validation (types, required fields, ranges)
- [x] Handle missing values with a documented strategy
- [x] Detect and resolve duplicate leads/interactions
- [x] Document data quality assumptions

## Phase 4 — Feature Engineering
- [x] Engagement features (`email_open_rate`, `click_rate`, `call_response_rate`)
- [x] Intent features (`pricing_page_visits`, `demo_requested`)
- [x] Recency features (`days_since_last_contact`)
- [x] Opportunity features (`opportunity_stage`, `deal_value`)
- [x] Account/profile features
- [x] Interaction-history features
- [x] Leakage audit — confirm no post-outcome information leaks into features

## Phase 5 — Baseline Scoring
- [x] Define simple rule-based scoring logic
- [x] Run baseline on the dataset
- [x] Record baseline performance metrics for later comparison

## Phase 6 — Train Candidate ML Models
- [x] Logistic Regression
- [x] Random Forest
- [x] Gradient Boosting
- [x] Proper train/validation/test split (time-aware if interaction history is time-dependent)

## Phase 7 — Evaluate & Compare Models
- [x] ROC-AUC, Precision, Recall, F1, Confusion Matrix per model
- [x] Probability calibration check
- [x] Precision@K, Recall@K, Top-K conversion rate, Lift
- [x] Conversion rate by score bucket
- [x] Compare all candidates + baseline; select and document the chosen model with rationale

## Phase 8 — SHAP Explainability
- [x] Integrate SHAP for the selected model
- [x] Generate top positive/negative factors per lead
- [x] Sanity-check explanations against known feature importances
- [x] Natural-language rationale generation derived from SHAP contributors (deterministic template)

## Phase 9 — Next-Best-Action Engine
- [x] Implement deterministic score-band rules (`CALL`, `EMAIL`, `DEMO`, `NURTURE`, `REVIEW`)
- [x] Define recommendation confidence separately from model probability
- [x] Unit test every score band and edge case
- [x] Document the rule set and its rationale

## Phase 10 — PostgreSQL Schema
- [ ] Design tables: `leads`, `interactions`, `predictions`, `recommendations`, `overrides`, `feedback`
- [ ] Define relationships (Lead → Interactions/Predictions/Recommendations/Overrides/Feedback)
- [ ] Write migrations (SQLModel)
- [ ] Seed with synthetic dataset

## Phase 11 — FastAPI APIs
- [x] `GET /health`
- [x] `GET /api/leads`
- [x] `GET /api/leads/{lead_id}`
- [x] `GET /api/leads/ranked`
- [x] `POST /api/leads/score`
- [x] `POST /api/leads/explain`
- [x] `POST /api/leads/recommend`
- [x] `POST /api/leads/intelligence`
- [x] Pydantic schemas for every request/response

## Phase 12 — Next.js Frontend
- [ ] App shell + navigation (per `design.md` layout)
- [ ] Dashboard page
- [ ] Ranked Leads page
- [ ] Lead Detail page (score, SHAP breakdown, explanation, timeline, accept/override)
- [ ] Analytics page
- [ ] `lib/api.ts` + `lib/types.ts` wired to backend
- [ ] TanStack Query integration for all server state

## Phase 13 — Human Override / Feedback
- [ ] Accept flow wired end to end
- [ ] Override flow (action + reason) wired end to end
- [ ] Feedback persisted correctly with `lead_id`, `original_action`, `override_action`, `reason`, `timestamp`
- [ ] Confirm no hidden auto-retraining is triggered by feedback capture

## Phase 14 — Integration Testing
- [ ] Backend unit tests (feature engineering, scoring, SHAP, recommendation rules, DB ops)
- [ ] API tests (`pytest` + `httpx`) for all endpoints
- [ ] End-to-end test scenarios: hot lead, cold lead, new lead, inactive lead, high-value lead, demo-requested lead, high engagement/low conversion history, low engagement/high opportunity value
- [ ] Frontend smoke test of full user flow (view ranked leads → open detail → accept/override)

## Phase 15 — Deployment
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to Render/Railway (or equivalent)
- [ ] Managed PostgreSQL provisioned
- [ ] Environment variables configured for production

## Phase 16 — Documentation / Demo / Portfolio
- [ ] `README.md` with problem statement, architecture summary, and setup instructions
- [ ] Model comparison + evaluation write-up (baseline vs. ML, with numbers)
- [ ] Demo script / recorded walkthrough
- [ ] Portfolio framing finalized: "Explainable AI system for CRM lead prioritization and next-best-action recommendations" — not "CRM dashboard built with Python"

---

## Current Status

**Overall stage:** FastAPI Backend (Phase 8 / Tasks Phase 11) complete. Thin route handlers, Pydantic DTOs, scoring, explanation, NBA, and ranked leads endpoints exposed.

**Next up:** PostgreSQL Schema & Database Persistence (Phase 10).
