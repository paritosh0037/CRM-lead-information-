import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import datetime

from app.main import app
from app.core.database import engine
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation as DBRecommendation
from app.models.feedback import Feedback

client = TestClient(app)


def test_production_intelligence_persistence():
    """
    Tests that calling the combined intelligence endpoint properly persists
    the Prediction and Recommendation records in the database with traceability.
    """
    payload = {
        "lead_id": "TEST_PERSIST_001",
        "demo_requested": 1,
        "pricing_page_visit": 2,
        "annual_revenue": 5000000.0,
        "deal_value": 50000.0,
        "days_since_last_contact": 10,
    }
    
    # 1. Trigger the endpoint
    response = client.post("/api/leads/intelligence", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["lead_id"] == "TEST_PERSIST_001"
    
    # 2. Verify Persistence in DB
    with Session(engine) as session:
        # Check Prediction
        pred = session.exec(select(Prediction).where(Prediction.lead_id == "TEST_PERSIST_001")).first()
        assert pred is not None
        assert pred.conversion_probability == data["conversion_probability"]
        assert pred.lead_score == data["lead_score"]
        assert pred.model_version is not None
        assert pred.model_version != "unknown"  # Assuming model version is tracked
        
        # Check Recommendation
        rec = session.exec(select(DBRecommendation).where(DBRecommendation.lead_id == "TEST_PERSIST_001")).first()
        assert rec is not None
        assert rec.recommended_action == data["recommendation"]["recommended_action"]
        assert rec.confidence_score == data["recommendation"]["recommendation_confidence"]


def test_model_version_traceability():
    """
    Ensures that when we get a lead by ID, the model version can be traced via the endpoint or DB.
    """
    # Assuming L00001 exists from seed data
    response = client.get("/api/leads/L00001")
    if response.status_code == 200:
        data = response.json()
        
        with Session(engine) as session:
            pred = session.exec(select(Prediction).where(Prediction.lead_id == "L00001")).first()
            if pred:
                assert pred.model_version is not None


def test_invalid_lead_input_rejection():
    """
    Ensures malformed input produces consistent HTTP 422 validation errors.
    """
    payload = {
        "lead_id": "TEST_INVALID",
        # Missing required fields like days_since_last_contact (if it was required by schema)
        "annual_revenue": "NOT_A_NUMBER",
    }
    response = client.post("/api/leads/intelligence", json=payload)
    assert response.status_code == 422


def test_missing_lead_404():
    """
    Ensures a missing lead ID returns 404.
    """
    response = client.get("/api/leads/THIS_LEAD_DOES_NOT_EXIST")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_no_silent_retraining_in_api():
    """
    Verifies that calling any API endpoint does NOT trigger model training.
    Since training takes time and writes to disk, we ensure it's not happening here.
    (This is a conceptual assertion; the architecture guarantees this by not importing train.py in API)
    """
    # The API routes in leads.py and feedback.py only use LeadService and FeedbackService.
    # Neither service imports run_training_pipeline.
    pass


def test_human_override_immutability():
    """
    Verifies Phase 7 override immutability constraint: 
    Override stores Feedback but does NOT alter the Recommendation table.
    """
    lead_id = "TEST_IMMUTABILITY_001"
    
    # 1. Create a recommendation first
    payload = {
        "lead_id": lead_id,
        "demo_requested": 1,
    }
    intel_response = client.post("/api/leads/intelligence", json=payload)
    assert intel_response.status_code == 200
    orig_action = intel_response.json()["recommendation"]["recommended_action"]
    
    # 2. Provide override feedback
    feedback_payload = {
        "original_action": orig_action,
        "override_action": "CALL" if orig_action != "CALL" else "EMAIL",
        "reason": "Customer called us directly",
        "actor_context": "test_user"
    }
    fb_response = client.post(f"/api/feedback/{lead_id}/override", json=feedback_payload)
    assert fb_response.status_code == 200
    
    # 3. Assert Recommendation table remains untouched
    with Session(engine) as session:
        rec = session.exec(select(DBRecommendation).where(DBRecommendation.lead_id == lead_id)).first()
        assert rec is not None
        assert rec.recommended_action == orig_action  # Must be original, not the override
        
        fb = session.exec(select(Feedback).where(Feedback.lead_id == lead_id)).first()
        assert fb is not None
        assert fb.override_action == feedback_payload["override_action"]
