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
