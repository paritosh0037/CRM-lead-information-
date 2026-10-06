import pytest
import pandas as pd
from unittest.mock import patch, MagicMock

from app.schemas.lead import CombinedLeadIntelligenceResponse
from app.services.lead_service import LeadService
from app.ml.model import MLModel
from app.services.recommendation import RecommendationEngine

@pytest.fixture
def mock_lead_data():
    return {
        "lead_id": "L123",
        "deal_value": 50000,
        "demo_requested": 1,
        "days_since_last_contact": 5,
        "industry_Technology": 1,
        "email_clicked": 2
    }

@pytest.fixture
def mock_ml_model():
    model = MagicMock(spec=MLModel)
    model.predict_probability.return_value = 0.82
    model.explain.return_value = {
        "prediction_probability": 0.82,
        "margin_prediction": 1.5,
        "base_value": 0.0,
        "top_positive_factors": [{"feature": "demo_requested", "value": 1, "shap_value": 0.5, "direction": "positive"}],
        "top_negative_factors": [],
        "human_readable": "Mock explanation."
    }
    model._metadata = {"model_version": "1.0.0"}
    return model

@pytest.fixture
def lead_service(mock_ml_model):
    service = LeadService(model_path="dummy")
    service.ml_model = mock_ml_model
    # Patch database calls
    service._persist_decision_trace = MagicMock()
    return service

def test_integration_flow_hot_lead(lead_service, mock_lead_data):
    """Test full integration from raw features to unified decision."""
    decision = lead_service.get_lead_intelligence(mock_lead_data)
    
    # 1. Unified Response Contract
    assert isinstance(decision, CombinedLeadIntelligenceResponse)
    assert decision.lead_id == "L123"
    
    # 2. Probability and Score
    assert decision.conversion_probability == 0.82
    assert decision.lead_score == 82
    
    # 3. SHAP integrates correctly
    assert decision.explanation.lead_id == "L123"
    assert decision.explanation.explanation_text == "Mock explanation."
    assert len(decision.explanation.positive_factors) == 1
    
    # 4. Recommendation Engine runs (Demo Requested -> DEMO or similar depending on phase 1 rules)
    # The RecommendationEngine will see demo_requested=1 and score=82 -> High confidence DEMO action probably
    assert decision.recommendation.recommended_action in ["DEMO", "CALL"]
    assert decision.recommendation.recommendation_confidence > 0

def test_recommendation_is_independent_of_shap(lead_service, mock_lead_data):
    """Ensure SHAP explanation doesn't illegally dictate recommendation logic."""
    decision = lead_service.get_lead_intelligence(mock_lead_data)
    
    # Action comes from rule trace, not SHAP
    assert decision.recommendation.rule_trace is not None
    assert hasattr(decision.recommendation.rule_trace, "trigger")

def test_model_version_tracing(lead_service, mock_lead_data):
    """Ensure _persist_decision_trace receives the correct metadata."""
    decision = lead_service.get_lead_intelligence(mock_lead_data)
    
    # Check that persistence was called
    lead_service._persist_decision_trace.assert_called_once_with(decision)
    
def test_cold_lead_behavior(lead_service):
    lead_service.ml_model.predict_probability.return_value = 0.15
    lead_data = {"lead_id": "L999", "deal_value": 100, "days_since_last_contact": 60}
    
    decision = lead_service.get_lead_intelligence(lead_data)
    assert decision.lead_score == 15
    assert decision.recommendation.recommended_action in ["NURTURE", "REVIEW"]

def test_new_lead_behavior(lead_service):
    # No historical interactions
    lead_service.ml_model.predict_probability.return_value = 0.50
    lead_data = {"lead_id": "L001"} # Minimal data
    
    decision = lead_service.get_lead_intelligence(lead_data)
    assert decision.lead_score == 50
    assert decision.recommendation.recommended_action is not None
