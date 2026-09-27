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


def test_score_ge_80_with_demo(engine):
    lead = {
        "lead_id": "L0001",
        "lead_score": 88,
        "conversion_probability": 0.88,
        "demo_requested": 1,
        "pricing_page_visit": 2,
    }
    rec = engine.recommend(lead)
    assert rec["recommended_action"] == ACTION_DEMO
    assert rec["recommended_action"] in VALID_ACTIONS
    assert rec["rule_trace"]["trigger"] == "demo_requested"
    assert "demo" in rec["rationale"].lower()
    assert len(rec["confidence_reasons"]) >= 2
    # Ensure confidence is separate from probability/score
    assert rec["recommendation_confidence"] != rec["conversion_probability"]
    assert rec["recommendation_confidence"] != rec["lead_score"]
    assert 0.5 <= rec["recommendation_confidence"] <= 1.0


def test_score_ge_80_without_demo(engine):
    lead = {
        "lead_id": "L0002",
        "lead_score": 85,
        "conversion_probability": 0.85,
        "demo_requested": 0,
        "days_since_last_contact": 10,
    }
    rec = engine.recommend(lead)
    assert rec["recommended_action"] == ACTION_CALL
    assert rec["rule_trace"]["trigger"] == "high_score_no_demo"
    assert "call" in rec["rationale"].lower()
    assert rec["recommended_action"] in VALID_ACTIONS


def test_score_60_to_79_high_email(engine):
    lead = {
        "lead_id": "L0003",
        "lead_score": 72,
        "conversion_probability": 0.72,
        "email_opened": 4,
        "email_clicked": 2,
        "days_since_last_contact": 30,
    }
    rec = engine.recommend(lead)
    assert rec["recommended_action"] == ACTION_EMAIL
    assert rec["rule_trace"]["trigger"] == "high_email_engagement"
    assert "email" in rec["rationale"].lower()


def test_score_60_to_79_recent_interaction_call(engine):
    lead = {
        "lead_id": "L0004",
        "lead_score": 68,
        "conversion_probability": 0.68,
        "email_opened": 0,
        "email_clicked": 0,
        "days_since_last_contact": 5,
        "call_made": 1,
        "total_interactions": 6,
    }
    rec = engine.recommend(lead)
    assert rec["recommended_action"] == ACTION_CALL
    assert rec["rule_trace"]["trigger"] == "strong_recent_interaction"


def test_score_40_to_59_nurture(engine):
    lead = {
        "lead_id": "L0005",
        "lead_score": 52,
        "conversion_probability": 0.52,
        "demo_requested": 1,  # Even with demo, mid-tier score defaults to nurture
    }
    rec = engine.recommend(lead)
    assert rec["recommended_action"] == ACTION_NURTURE
    assert "nurture" in rec["rationale"].lower()
    assert "40-59" in rec["rule_trace"]["score_band"]


def test_score_below_40_nurture(engine):
    lead = {
        "lead_id": "L0006",
        "lead_score": 25,
        "conversion_probability": 0.25,
    }
    rec = engine.recommend(lead)
    assert rec["recommended_action"] == ACTION_NURTURE
    assert "0-39" in rec["rule_trace"]["score_band"]


def test_score_boundaries(engine):
    # Boundary 80
    rec_80 = engine.recommend({"lead_score": 80, "demo_requested": 0})
    assert rec_80["recommended_action"] == ACTION_CALL

    # Boundary 79
    rec_79 = engine.recommend({"lead_score": 79, "email_opened": 3})
    assert rec_79["recommended_action"] == ACTION_EMAIL

    # Boundary 60
    rec_60 = engine.recommend({"lead_score": 60, "days_since_last_contact": 30})
    assert rec_60["recommended_action"] in [ACTION_EMAIL, ACTION_CALL]

    # Boundary 59
    rec_59 = engine.recommend({"lead_score": 59})
    assert rec_59["recommended_action"] == ACTION_NURTURE

    # Boundary 40
    rec_40 = engine.recommend({"lead_score": 40})
    assert rec_40["recommended_action"] == ACTION_NURTURE

    # Boundary 39
    rec_39 = engine.recommend({"lead_score": 39})
    assert rec_39["recommended_action"] == ACTION_NURTURE


def test_missing_optional_signals_safe_fallback(engine):
    # Minimal input with only lead_id and score
    rec = engine.recommend({"lead_id": "L_EMPTY", "lead_score": 85})
    assert rec["recommended_action"] in VALID_ACTIONS
    assert rec["lead_id"] == "L_EMPTY"
    assert rec["lead_score"] == 85
    assert len(rec["confidence_reasons"]) > 0


def test_recommend_batch_dataframe(engine):
    df = pd.DataFrame(
        [
            {"lead_id": "L1", "lead_score": 90, "demo_requested": 1},
            {"lead_id": "L2", "lead_score": 75, "email_clicked": 2},
            {"lead_id": "L3", "lead_score": 45},
            {"lead_id": "L4", "lead_score": 20},
        ]
    )
    batch_results = engine.recommend_batch(df)
    assert len(batch_results) == 4
    assert batch_results[0]["recommended_action"] == ACTION_DEMO
    assert batch_results[1]["recommended_action"] == ACTION_EMAIL
    assert batch_results[2]["recommended_action"] == ACTION_NURTURE
    assert batch_results[3]["recommended_action"] == ACTION_NURTURE
