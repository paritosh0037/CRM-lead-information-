import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from app.ml.feature_engineering import engineer_features

@pytest.fixture
def sample_leads():
    return pd.DataFrame([
        {
            "lead_id": "L1",
            "annual_revenue": 100000,
            "budget": 50000,
            "deal_value": 20000,
            "industry": "Tech",
            "company_size": "Enterprise",
            "lead_source": "Organic",
            "opportunity_stage": "Prospecting",
            "converted": 1,
            "race": "Unknown",
            "gender": "Unknown",
            "days_since_last_contact": 10
        },
        {
            "lead_id": "L2",
            "annual_revenue": -100, # Invalid
            "budget": None, # Missing
            "deal_value": -500, # Invalid
            "industry": None, # Missing
            "company_size": "SMB",
            "lead_source": "Paid",
            "opportunity_stage": "Closed Won", # Leakage risk
            "converted": 1,
            "days_since_last_contact": -5 # Invalid
        },
        {
            "lead_id": "L3",
            "annual_revenue": 50000,
            "budget": 10000,
            "deal_value": 5000,
            "industry": "Finance",
            "company_size": "Mid-Market",
            "lead_source": "Organic",
            "opportunity_stage": "Negotiation",
            "converted": 0,
            "days_since_last_contact": 20
        }
    ])

@pytest.fixture
def sample_interactions():
    base_time = datetime.now(timezone.utc)
    return pd.DataFrame([
        {
            "lead_id": "L1",
            "interaction_type": "email_opened",
            "interaction_date": base_time - timedelta(days=5),
            "duration_seconds": 0
        },
        {
            "lead_id": "L1",
            "interaction_type": "demo_requested",
            "interaction_date": base_time + timedelta(days=2), # Future interaction
            "duration_seconds": 0
        },
        {
            "lead_id": "L2",
            "interaction_type": "call_made",
            "interaction_date": base_time - timedelta(days=1),
            "duration_seconds": 120
        }
    ])

def test_prediction_time_filtering(sample_leads, sample_interactions):
    prediction_timestamp = datetime.now(timezone.utc)
    features, target, ids = engineer_features(sample_leads, sample_interactions, prediction_timestamp)
    
    # L1 should have email_opened=1, but demo_requested=0 because demo was in the future
    l1_features = features[ids == "L1"].iloc[0]
    assert l1_features["email_opened"] == 1
    assert l1_features["demo_requested"] == 0

def test_no_prediction_time_includes_all(sample_leads, sample_interactions):
    features, target, ids = engineer_features(sample_leads, sample_interactions)
    
    # Without timestamp filtering, all interactions are included
    l1_features = features[ids == "L1"].iloc[0]
    assert l1_features["email_opened"] == 1
    assert l1_features["demo_requested"] == 1

def test_historical_aggregation_and_defaults(sample_leads, sample_interactions):
    prediction_timestamp = datetime.now(timezone.utc)
    features, target, ids = engineer_features(sample_leads, sample_interactions, prediction_timestamp)
    
    # L2 should have call_made=1 and total_web_duration=120
    l2_features = features[ids == "L2"].iloc[0]
    assert l2_features["call_made"] == 1
    assert l2_features["total_web_duration"] == 120
    
    # L3 has no interactions, should default to 0
    l3_features = features[ids == "L3"].iloc[0]
    assert l3_features["email_opened"] == 0
    assert l3_features["call_made"] == 0
    assert l3_features["total_interactions"] == 0

def test_target_exclusion(sample_leads, sample_interactions):
    features, target, ids = engineer_features(sample_leads, sample_interactions)
    
    assert "converted" not in features.columns
    assert target.name == "converted"
    assert (target == pd.Series([1, 1, 0])).all()

def test_leakage_opportunity_stage(sample_leads, sample_interactions):
    features, target, ids = engineer_features(sample_leads, sample_interactions)
    
    # L2 had opportunity_stage = "Closed Won", which is leakage. Should be mapped to Unknown
    # Verify 'opportunity_stage_Closed Won' does not exist
    assert "opportunity_stage_Closed Won" not in features.columns
    # Check if L2's opportunity stage was mapped to Unknown
    assert "opportunity_stage_Unknown" in features.columns
    assert features[ids == "L2"].iloc[0]["opportunity_stage_Unknown"] == 1

def test_protected_attributes_excluded(sample_leads, sample_interactions):
    features, target, ids = engineer_features(sample_leads, sample_interactions)
    assert "race" not in features.columns
    assert "gender" not in features.columns

def test_missing_and_invalid_values(sample_leads, sample_interactions):
    features, target, ids = engineer_features(sample_leads, sample_interactions)
    
    l2_features = features[ids == "L2"].iloc[0]
    # budget was None, should be 0.0
    assert l2_features["budget"] == 0.0
    # annual_revenue was negative, should be 0.0
    assert l2_features["annual_revenue"] == 0.0
    # deal_value was negative, should be 0.0
    assert l2_features["deal_value"] == 0.0
    # days_since_last_contact was negative, should be coerced to NaN and then filled with 999.0
    assert l2_features["days_since_last_contact"] == 999.0
    # industry was missing, should be mapped to Unknown
    assert l2_features["industry_Unknown"] == 1

def test_determinism(sample_leads, sample_interactions):
    prediction_timestamp = datetime.now(timezone.utc)
    features1, target1, ids1 = engineer_features(sample_leads, sample_interactions, prediction_timestamp)
    features2, target2, ids2 = engineer_features(sample_leads, sample_interactions, prediction_timestamp)
    
    pd.testing.assert_frame_equal(features1, features2)
    pd.testing.assert_series_equal(target1, target2)
    pd.testing.assert_series_equal(ids1, ids2)

def test_no_interactions_dataframe(sample_leads):
    # Test behavior when interactions dataframe is empty
    empty_interactions = pd.DataFrame(columns=["lead_id", "interaction_type", "interaction_date", "duration_seconds"])
    features, target, ids = engineer_features(sample_leads, empty_interactions)
    
    assert "email_opened" in features.columns
    assert (features["email_opened"] == 0).all()
