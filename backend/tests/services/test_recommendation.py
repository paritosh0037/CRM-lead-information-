import pandas as pd
import pytest

from app.services.recommendation import (
    ACTION_CALL,
    ACTION_DEMO,
    ACTION_EMAIL,
    ACTION_NURTURE,
    ACTION_REVIEW,
    VALID_ACTIONS,
    RecommendationEngine,
)

@pytest.fixture
def engine():
    return RecommendationEngine()

def test_missing_lead_score_and_prob(engine):
    res = engine.recommend({"lead_id": "L1"})
    assert res["recommended_action"] == ACTION_REVIEW
    assert "missing_score" in res["rule_trace"]["trigger"]
    assert res["recommendation_confidence"] == 0.50

def test_invalid_lead_score_negative(engine):
    res = engine.recommend({"lead_id": "L2", "lead_score": -10, "conversion_probability": 0.0})
    assert res["recommended_action"] == ACTION_REVIEW
    assert res["rule_trace"]["score_band"] == "Invalid"

def test_invalid_lead_score_high(engine):
    res = engine.recommend({"lead_id": "L3", "lead_score": 105, "conversion_probability": 1.0})
    assert res["recommended_action"] == ACTION_REVIEW

def test_invalid_probability(engine):
    res = engine.recommend({"lead_id": "L4", "lead_score": 50, "conversion_probability": 1.5})
    assert res["recommended_action"] == ACTION_REVIEW

def test_hot_lead_call(engine):
    res = engine.recommend({"lead_id": "L5", "lead_score": 85})
    assert res["recommended_action"] == ACTION_CALL
    assert "80-100" in res["rule_trace"]["score_band"]
    assert res["recommendation_confidence"] >= 0.85

def test_hot_lead_demo(engine):
    res = engine.recommend({"lead_id": "L6", "lead_score": 85, "demo_requested": 1})
    assert res["recommended_action"] == ACTION_DEMO
    assert "demo_requested" in res["rule_trace"]["trigger"]

def test_warm_opportunity_email(engine):
    # 60-79 score, high email engagement
    res = engine.recommend({
        "lead_id": "L7",
        "lead_score": 70,
        "email_opened": 5,
        "email_clicked": 2,
        "days_since_last_contact": 30 # No recent interaction
    })
    assert res["recommended_action"] == ACTION_EMAIL
    assert "high_email_engagement" in res["rule_trace"]["trigger"]

def test_warm_opportunity_call(engine):
    # 60-79 score, high recent interaction
    res = engine.recommend({
        "lead_id": "L8",
        "lead_score": 75,
        "days_since_last_contact": 5,
        "total_interactions": 6
    })
    assert res["recommended_action"] == ACTION_CALL
    assert "strong_recent_interaction" in res["rule_trace"]["trigger"]

def test_mid_funnel_nurture(engine):
    res = engine.recommend({"lead_id": "L9", "lead_score": 50})
    assert res["recommended_action"] == ACTION_NURTURE
    assert "40-59" in res["rule_trace"]["score_band"]

def test_mid_funnel_demo(engine):
    # Moderate score but requested demo
    res = engine.recommend({"lead_id": "L10", "lead_score": 55, "demo_requested": 1})
    assert res["recommended_action"] == ACTION_DEMO

def test_cold_lead_nurture(engine):
    res = engine.recommend({"lead_id": "L11", "lead_score": 30})
    assert res["recommended_action"] == ACTION_NURTURE
    assert "0-39" in res["rule_trace"]["score_band"]

def test_high_value_escalation(engine):
    res = engine.recommend({
        "lead_id": "L12",
        "lead_score": 45,
        "deal_value": 150000.0
    })
    assert res["recommended_action"] == ACTION_CALL
    assert res["rule_trace"]["score_band"] == "High-Value Escalation"
    assert res["recommendation_confidence"] == 0.90

def test_high_value_ignored_if_score_too_low(engine):
    res = engine.recommend({
        "lead_id": "L13",
        "lead_score": 30, # < 40
        "deal_value": 150000.0
    })
    assert res["recommended_action"] == ACTION_NURTURE
    assert "0-39" in res["rule_trace"]["score_band"]

def test_stale_contact_penalty(engine):
    res = engine.recommend({
        "lead_id": "L14",
        "lead_score": 85,
        "days_since_last_contact": 100
    })
    assert res["recommended_action"] == ACTION_CALL
    assert "Stale contact recency (> 90 days)" in str(res["confidence_reasons"])
    # Base confidence for >=80 is 0.85, minus 0.05 for stale
    assert res["recommendation_confidence"] == 0.80

def test_new_lead(engine):
    # No interaction history, but has a probability
    res = engine.recommend({
        "lead_id": "L15",
        "conversion_probability": 0.65
    })
    # Implied score = 65
    assert res["lead_score"] == 65
    assert res["recommended_action"] == ACTION_EMAIL
    assert "moderate_score_standard_nurture_email" in res["rule_trace"]["trigger"]

def test_rule_priority_conflict(engine):
    # High email engagement AND recent interaction
    # Recent interaction should prioritize CALL over EMAIL, except if email is very high
    # Actually logic: if high_email and not (recent_interaction and <= 7 days) -> EMAIL
    res = engine.recommend({
        "lead_id": "L16",
        "lead_score": 75,
        "email_opened": 10,
        "email_clicked": 5,
        "days_since_last_contact": 2, # highly recent
        "total_interactions": 10
    })
    # Because days <= 7, high email block is skipped, goes to recent interaction (CALL)
    assert res["recommended_action"] == ACTION_CALL
    assert "strong_recent_interaction" in res["rule_trace"]["trigger"]

def test_confidence_clamping(engine):
    # High score + demo + pricing -> high confidence
    res = engine.recommend({
        "lead_id": "L17",
        "lead_score": 95,
        "deal_value": 500000.0, # High value adds 0.90
    })
    assert res["recommended_action"] == ACTION_CALL
    assert res["recommendation_confidence"] <= 0.95

def test_recommend_batch_dataframe(engine):
    df = pd.DataFrame(
        [
            {"lead_id": "L1", "lead_score": 90, "demo_requested": 1},
            {"lead_id": "L2", "lead_score": 75, "email_clicked": 2},
            {"lead_id": "L3", "lead_score": 45},
            {"lead_id": "L4", "lead_score": 20},
            {"lead_id": "L5", "lead_score": None, "conversion_probability": None}, # Missing
        ]
    )
    batch_results = engine.recommend_batch(df)
    assert len(batch_results) == 5
    assert batch_results[0]["recommended_action"] == ACTION_DEMO
    assert batch_results[1]["recommended_action"] == ACTION_EMAIL
    assert batch_results[2]["recommended_action"] == ACTION_NURTURE
    assert batch_results[3]["recommended_action"] == ACTION_NURTURE
    assert batch_results[4]["recommended_action"] == ACTION_REVIEW
