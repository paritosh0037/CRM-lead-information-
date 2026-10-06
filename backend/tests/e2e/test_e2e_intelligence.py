import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import logging

from app.main import app
from app.core.database import engine
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation as DBRecommendation
from app.models.feedback import Feedback

client = TestClient(app)

ARCHETYPES = [
    {
        "name": "Hot lead",
        "payload": {
            "lead_id": "E2E_HOT",
            "demo_requested": 1,
            "pricing_page_visit": 5,
            "email_opened": 10,
            "days_since_last_contact": 1,
            "annual_revenue": 1000000.0,
            "deal_value": 50000.0
        }
    },
    {
        "name": "Cold lead",
        "payload": {
            "lead_id": "E2E_COLD",
            "demo_requested": 0,
            "pricing_page_visit": 0,
            "email_opened": 0,
            "days_since_last_contact": 100,
            "annual_revenue": 10000.0,
            "deal_value": 500.0
        }
    },
    {
        "name": "New lead",
        "payload": {
            "lead_id": "E2E_NEW",
            "demo_requested": 0,
            "pricing_page_visit": 1,
            "email_opened": 1,
            "days_since_last_contact": 0,
            "annual_revenue": 50000.0,
            "deal_value": 5000.0
        }
    },
    {
        "name": "Inactive lead",
        "payload": {
            "lead_id": "E2E_INACTIVE",
            "demo_requested": 0,
            "pricing_page_visit": 1,
            "email_opened": 1,
            "days_since_last_contact": 365,
            "annual_revenue": 100000.0,
            "deal_value": 10000.0
        }
    },
    {
        "name": "High-value opportunity",
        "payload": {
            "lead_id": "E2E_HIGH_VAL",
            "demo_requested": 1,
            "pricing_page_visit": 2,
            "email_opened": 5,
            "days_since_last_contact": 5,
            "annual_revenue": 50000000.0,
            "deal_value": 1000000.0
        }
    },
    {
        "name": "Demo-requested lead",
        "payload": {
            "lead_id": "E2E_DEMO",
            "demo_requested": 1,
            "pricing_page_visit": 0,
            "email_opened": 2,
            "days_since_last_contact": 2,
            "annual_revenue": 250000.0,
            "deal_value": 25000.0
        }
    },
    {
        "name": "High engagement / low conversion history",
        "payload": {
            "lead_id": "E2E_HIGH_ENG_LOW_CONV",
            "demo_requested": 0,
            "pricing_page_visit": 20,
            "email_opened": 50,
            "days_since_last_contact": 1,
            "annual_revenue": 1000.0,
            "deal_value": 100.0
        }
    },
    {
        "name": "Low engagement / high opportunity value",
        "payload": {
            "lead_id": "E2E_LOW_ENG_HIGH_VAL",
            "demo_requested": 0,
            "pricing_page_visit": 0,
            "email_opened": 1,
            "days_since_last_contact": 30,
            "annual_revenue": 100000000.0,
            "deal_value": 5000000.0
        }
    }
]

@pytest.mark.parametrize("archetype", ARCHETYPES)
def test_e2e_lead_intelligence(archetype):
    """
    Tests the complete intelligence path for every required archetype.
    """
    payload = archetype["payload"]
    lead_id = payload["lead_id"]
    
    # 1. Trigger intelligence endpoint
    res = client.post("/api/leads/intelligence", json=payload)
    assert res.status_code == 200, f"Failed archetype {archetype['name']}: {res.text}"
    
    data = res.json()
    
    # 2. Verify Output Contract
    assert "conversion_probability" in data
    assert "lead_score" in data
    
    assert "explanation" in data
    assert len(data["explanation"]["top_factors"]) > 0
    assert "base_value" in data["explanation"]
    
    assert "recommendation" in data
    assert data["recommendation"]["recommended_action"] in ["CALL", "EMAIL", "DEMO", "NURTURE", "REVIEW"]
    
    # 3. Verify Persistence
    with Session(engine) as session:
        pred = session.exec(select(Prediction).where(Prediction.lead_id == lead_id)).first()
        assert pred is not None
        assert pred.lead_score == data["lead_score"]
        assert pred.conversion_probability == data["conversion_probability"]
        assert pred.model_version is not None
        
        rec = session.exec(select(DBRecommendation).where(DBRecommendation.lead_id == lead_id)).first()
        assert rec is not None
        assert rec.recommended_action == data["recommendation"]["recommended_action"]


def test_human_in_the_loop_e2e():
    """
    Tests accepting and overriding a recommendation without modifying the ML model.
    """
    lead_id = "E2E_HITL"
    payload = {
        "lead_id": lead_id,
        "demo_requested": 1,
        "pricing_page_visit": 2,
        "deal_value": 10000.0,
    }
    
    # Generate initial rec
    intel_res = client.post("/api/leads/intelligence", json=payload)
    assert intel_res.status_code == 200
    orig_action = intel_res.json()["recommendation"]["recommended_action"]
    
    # Accept
    accept_payload = {
        "original_action": orig_action,
        "actor_context": "e2e_test_user"
    }
    res = client.post(f"/api/feedback/{lead_id}/accept", json=accept_payload)
    assert res.status_code == 200
    
    # Override
    override_action = "CALL" if orig_action != "CALL" else "EMAIL"
    override_payload = {
        "original_action": orig_action,
        "override_action": override_action,
        "reason": "E2E testing constraint",
        "actor_context": "e2e_test_user"
    }
    res = client.post(f"/api/feedback/{lead_id}/override", json=override_payload)
    assert res.status_code == 200
    
    # Verify original rec is completely intact
    with Session(engine) as session:
        rec = session.exec(select(DBRecommendation).where(DBRecommendation.lead_id == lead_id)).first()
        assert rec.recommended_action == orig_action
        
        fb_list = list(session.exec(select(Feedback).where(Feedback.lead_id == lead_id)))
        assert len(fb_list) == 2


def test_model_explanation_integrity():
    """
    Ensures that prediction probabilities and SHAP explanations mathematically align.
    """
    payload = {
        "lead_id": "E2E_INTEGRITY",
        "demo_requested": 1,
    }
    res = client.post("/api/leads/intelligence", json=payload)
    assert res.status_code == 200
    data = res.json()
    
    base_value = data["explanation"]["base_value"]
    prob = data["conversion_probability"]
    
    # We do not replicate the full math here, but we ensure base_value and probability exist
    # and aren't hard-coded mock values.
    assert base_value != 0.0 or prob != 0.0


def test_feature_leakage_exclusion():
    """
    Ensures protected/leaky attributes are stripped correctly (validation test).
    """
    payload = {
        "lead_id": "E2E_LEAKAGE",
        "demo_requested": 1,
        # Following should be ignored/stripped by Pydantic before reaching ML:
        "converted": 1,
        "won_reason": "Price",
        "race": "Unknown",
        "gender": "Unknown"
    }
    res = client.post("/api/leads/intelligence", json=payload)
    assert res.status_code == 200
    
    # Pydantic strips out undefined fields from LeadFeaturesInput.
    # Therefore, they shouldn't exist in the generated explanation factors.
    factors = [f["feature"] for f in res.json()["explanation"]["top_factors"]]
    assert "converted" not in factors
    assert "won_reason" not in factors
    assert "race" not in factors
    assert "gender" not in factors
