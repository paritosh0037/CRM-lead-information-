# Product Requirements Document (PRD)

## Project: AI-Powered CRM Lead Prioritization & Next-Best-Action System

---

## 1. Project Identity

**Name:** AI-Powered CRM Lead Prioritization & Next-Best-Action System
**Type:** Explainable machine-learning sales intelligence platform
**Intended use:** Hackathon project → ML portfolio piece → resume project → something defensible in technical interviews

**Positioning statement (use this, not a weaker one):**
> "Explainable AI system for CRM lead prioritization and next-best-action recommendations."

Not: *"CRM dashboard built with Python."*

### Non-negotiable constraint
Do not build a fake "AI dashboard" where an LLM invents scores. The core intelligence must be **measurable, reproducible, explainable, and evaluated**.

---

## 2. Core Problem

Sales teams cannot manually evaluate every lead with equal depth. The system helps reps focus on stronger opportunities while showing evidence for every recommendation.

Five questions the product must answer for every lead:

1. How promising is this lead?
2. Why did the system give it this score?
3. What should the salesperson do next?
4. Does the salesperson agree with the recommendation?
5. What happened after the recommendation?

---

## 3. Goals

The system must, for each lead:

- Calculate a lead-quality / conversion score
- Rank leads for sales follow-up
- Recommend the next best sales action
- Explain why a lead received its score and recommendation
- Provide pipeline analytics
- Allow sales users to override AI recommendations
- Capture human feedback for later model evaluation / improvement

## 4. Non-Goals (v1)

- No automatic model retraining loop (feedback is stored, not consumed automatically)
- No microservices, Kafka, Kubernetes, Redis, or Celery unless a concrete requirement appears later
- No deep learning for the core tabular scoring problem
- No use of protected/sensitive attributes anywhere in modeling

---

## 5. Users

**Primary user:** Sales representative — views ranked leads, reads the explanation, accepts or overrides the recommended action.

**Secondary user (implicit):** Sales/RevOps lead — consumes the analytics view (pipeline value, conversion funnel, score distribution) to judge whether the system is useful.

---

## 6. Core User Flow

```
CRM Data → Data Validation/Cleaning → Feature Engineering → Baseline Model → ML Model
→ Conversion Probability → Lead Score (0–100) → Explainability (SHAP)
→ Next-Best-Action Engine → Recommendation + Confidence + Rationale
→ FastAPI → Next.js Dashboard → Sales User → Accept/Override → Feedback
→ PostgreSQL → Future Model Evaluation/Improvement
```

Key distinction to preserve everywhere in the product and docs:
- **Next.js** = frontend/UI
- **FastAPI** = backend API / communication layer
- **ML Engine** = prediction and ML logic
- **Recommendation Engine** = business decision logic (separate from the ML model)
- **PostgreSQL** = persistent database
- **Feedback system** = human-in-the-loop data capture

---

## 7. Functional Requirements

### 7.1 Lead Scoring
- Model outputs a conversion probability (e.g. 0.87)
- Lead score = probability × 100 (e.g. 87)
- Model probability, lead score, and recommendation confidence are **three distinct values** — never conflate them

### 7.2 Explainability
- Every score must ship with a SHAP-based, feature-level explanation
- Explanation must list top positive and negative contributing factors with their impact
- The natural-language summary shown to the user must be **derived from the SHAP output**, not invented by an LLM. An LLM may only be used, optionally, to phrase the explanation more naturally — never to generate the underlying reasoning.

Example target output:

```
Lead Score: 87
Positive factors: Demo requested (+18), Pricing visits (+12), Email engagement (+10), Deal value (+6)
Negative factors: No recent reply (-5), Low recency (-4)

"High conversion potential because the lead requested a demo, repeatedly visited the
pricing page, and engaged with recent emails. Lack of recent phone engagement reduced
the score."
```

### 7.3 Next-Best-Action Engine
- Deterministic, transparent rules — not a black box
- Possible actions: `CALL`, `EMAIL`, `DEMO`, `NURTURE`, `REVIEW`
- Starting rule set (score-band based):
  - **≥ 80:** demo requested → `DEMO`; otherwise → `CALL`
  - **60–79:** high email engagement → `EMAIL`; strong recent interaction → `CALL`
  - **40–59:** `NURTURE`
  - **< 40:** long-term `NURTURE`
- Future inputs to incorporate: intent, engagement, recency, opportunity stage, previous communication, customer preferences, action history
- Recommendation confidence is a **separate, explicitly defined value** from model probability (e.g. based on rule strength / signal agreement), with its own listed reasons

### 7.4 Human-in-the-Loop
- Every recommendation can be **accepted** or **overridden**
- On override: capture the chosen action + a free-text reason
- Store: `lead_id`, `original_action`, `override_action`, `reason`, `timestamp`
- No automatic retraining on this feedback in v1 — it is stored for later evaluation

### 7.5 Analytics
Dashboard-level aggregate views (see `design.md` for layout):
- Total leads, high-priority leads, pipeline value, average lead score
- Score distribution, conversion funnel
- Score by opportunity stage
- Lead sources breakdown
- Action distribution
- High-risk / high-value pipeline segments

### 7.6 Model Evaluation (product-visible)
The product must be able to demonstrate, not just claim, that ranking is useful:
- Example target proof point: top 10% highest-scored leads convert at ~31% vs ~8% baseline across all leads
- Metrics tracked: ROC-AUC, Precision, Recall, F1, Confusion Matrix, Precision@K, Recall@K, Top-K conversion rate, Lift, conversion rate by score bucket, calibration

---

## 8. Data Requirements

- Synthetic CRM data is allowed and preferred if no suitable public dataset exists
- Target size: **2,000–5,000** realistic lead records (scalable to 50K+ if hardware allows)
- Synthetic data must contain realistic behavioral sequences (a lead's day-by-day interaction history), not meaningless random rows
- Core field groups: account/profile (company size, industry, revenue, budget, source), engagement (emails, calls, web visits), intent (pricing visits, demo requests), recency (days since last contact), opportunity (stage, deal value), history (previous purchase), and label (`converted`)
- **Prohibited fields:** race, religion, ethnicity, caste, gender, or any other protected/sensitive attribute — the model must never use these for decision-making

---

## 9. Success Criteria

The project is successful if it can demonstrate, end to end:

1. A real, evaluated ML model that beats a stated baseline
2. Explanations that are traceable to actual model behavior (not fabricated)
3. A working accept/override loop with feedback capture
4. A dashboard a sales rep could plausibly use
5. A README/demo that lets a technical interviewer follow the reasoning from raw CRM data to recommendation

## 10. Out of Scope / Explicit Anti-Patterns

- LLM as the primary scoring mechanism
- Unnecessary infrastructure (queues, container orchestration) before there's a concrete need
- Skipping baseline comparison or evaluation to "get to the UI faster"
- Presenting the SHAP-driven explanation as if it were free-form LLM reasoning
