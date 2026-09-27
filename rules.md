# Coding Rules

## Project: AI-Powered CRM Lead Prioritization & Next-Best-Action System

These rules exist to keep the project defensible in a technical interview. When in doubt, favor the option that is more measurable, more transparent, and less clever.

---

## 1. Core Engineering Principles

1. Build the ML system first, not the dashboard first.
2. Establish a baseline before claiming ML improvement.
3. Prevent data leakage — never use information that would only be known after the prediction point.
4. Keep explanations tied to actual model behavior (SHAP-derived, never invented).
5. Keep recommendations transparent — deterministic rules over black-box logic in v1.
6. Separate model probability, lead score, and recommendation confidence. They are related but never interchangeable.
7. Keep human override available at all times — never remove the accept/override path.
8. Store feedback instead of pretending automatic learning exists. No silent auto-retraining.
9. Keep FastAPI as the one API layer between frontend and everything else.
10. Keep ML logic separate from API routes (`ml/` vs `api/`).
11. Keep frontend separate from backend intelligence — no scoring or recommendation logic in Next.js.
12. Prefer measurable evidence over AI-generated claims — every dashboard claim should trace to a stored metric.
13. Avoid unnecessary infrastructure (no Kafka/Kubernetes/Redis/Celery without a concrete need).
14. Test everything important (see section 6).
15. Document design decisions and trade-offs as you make them, not retroactively.

---

## 2. Layering Rules (Backend)

- **`api/`** — thin route handlers only: parse request, call a service, return a response. No business logic, no ML calls, no raw SQL.
- **`services/`** — all business/orchestration logic (e.g. combining a prediction with recommendation rules). Services call `ml/` and `models/`, never the other way around.
- **`ml/`** — all model, feature engineering, scoring, and explainability code. Pure functions where possible; no FastAPI imports here.
- **`models/`** — SQLModel/ORM table definitions only.
- **`core/`** — config and database setup, no business logic.

Never let a route import from `ml/` directly — always go through a service.

---

## 3. ML-Specific Rules

- Do not let an LLM generate the lead score or the SHAP explanation content. An LLM, if used, only rewords an already-computed explanation.
- Always compare a candidate model against the rule-based baseline before presenting results.
- Log evaluation metrics (ROC-AUC, Precision, Recall, F1, Precision@K, Lift, calibration) for every trained model version — don't overwrite old results silently.
- Use time-aware splitting instead of random splitting whenever interaction history is time-dependent.
- Never include protected/sensitive attributes (race, religion, ethnicity, caste, gender, or similar) as model inputs, even transformed or proxied.
- Persist trained models with `joblib` and version them (e.g. filename or metadata includes date/metric summary) so a run is reproducible.

---

## 4. API Design Rules

- All endpoints return typed responses defined via Pydantic schemas — no ad hoc dicts.
- Validate all input with Pydantic; reject malformed CRM records with clear error messages rather than silently coercing them.
- Keep response shape consistent with the documented example in `architecture.md` (`score`, `conversion_probability`, `recommended_action`, `recommendation_confidence`, `top_factors`).
- Every write endpoint (`/override`, `/feedback`) must persist a timestamp and the actor context available at the time (lead_id, original vs. new action, reason).

---

## 5. Frontend Rules

- No fetch calls scattered through components — all API access goes through `lib/api.ts`.
- Shared types (matching backend Pydantic schemas) live in `lib/types.ts`. Keep them in sync manually until/unless a shared schema generator is introduced.
- Use TanStack Query for all server-state; don't hand-roll `useEffect` fetch/loading/error logic.
- Business/domain logic (e.g. score-band thresholds, action colors) is UI presentation only — thresholds and rules themselves are computed server-side and simply rendered here.
- Keep components composed by responsibility (`dashboard/`, `leads/`, `charts/`, `recommendations/`, `ui/`) — don't dump feature logic into `app/` page files.

---

## 6. Testing Rules

Required coverage areas:
- Feature engineering functions (unit tests with known inputs/outputs)
- Model prediction and scoring (deterministic given a fixed model artifact + seed)
- SHAP output shape and sanity (top factors sum roughly to the score delta from baseline)
- Recommendation rule engine (every score band and edge case)
- API endpoints (status codes, schema shape, error handling)
- Database operations (create/read/update for each table)
- Override behavior (persists correctly, doesn't mutate the original recommendation)
- Feedback capture (persists correctly, doesn't trigger any hidden retraining)
- End-to-end flow (CRM record in → recommendation out)

Required test scenarios (lead archetypes): hot lead, cold lead, new lead, inactive lead, high-value lead, demo-requested lead, high engagement/low conversion history, low engagement/high opportunity value.

Use `pytest` + `httpx` for backend tests.

---

## 7. Git / Collaboration Rules

- Do not let two AI coding tools (e.g. Codex and Antigravity) modify the same files simultaneously.
- Assign tools by role, not randomly:
  - Research → Perplexity
  - Architecture / reasoning / debugging → ChatGPT
  - Frontend design → Stitch
  - Implementation → Codex OR Antigravity (not both on the same file)
  - API testing → Bruno
  - Database inspection → Beekeeper Studio
  - Version control → Git + GitHub
- Commit messages should reference the phase/task from `tasks.md` they correspond to.
- Don't skip evaluation or data-quality stages just to reach the UI faster — this is the most common way this type of project loses defensibility.

---

## 8. Documentation Rules

- Every non-obvious design decision (why this model, why this threshold, why this rule) gets a one- or two-line note in commit messages or `architecture.md`, not left implicit in code.
- Keep this rules file, `architecture.md`, and `tasks.md` updated as the project evolves — stale docs are worse than no docs for an interview defense.
