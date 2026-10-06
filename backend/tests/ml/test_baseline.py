import pytest
import pandas as pd
import numpy as np

from app.ml.baseline import RuleBasedBaseline

@pytest.fixture
def baseline():
    return RuleBasedBaseline(base_prob=0.15)


def test_score_range(baseline):
    """Every valid input produces a score between the defined minimum and maximum."""
    # Test with minimum possible inputs
    df_min = pd.DataFrame([{
        "days_since_last_contact": 100,
        "demo_requested": 0,
        "pricing_page_visit": 0,
        "email_clicked": 0,
        "deal_value": 0,
        "annual_revenue": 0
    }])
    
    # Test with maximum possible inputs
    df_max = pd.DataFrame([{
        "demo_requested": 1,
        "pricing_page_visit": 1,
        "email_clicked": 10,
        "call_made": 10,
        "web_visit": 20,
        "days_since_last_contact": 10,
        "previous_purchase": 1,
        "opportunity_stage_Qualified": 1,
        "opportunity_stage_Proposal": 1,
        "deal_value": 200000,
        "annual_revenue": 2000000
    }])
    
    score_min = baseline.score(df_min)[0]
    score_max = baseline.score(df_max)[0]
    
    assert 0 <= score_min <= 100
    assert 0 <= score_max <= 100
    assert score_min < score_max


def test_determinism(baseline):
    """Same input produces exactly the same score."""
    df = pd.DataFrame([{
        "demo_requested": 1,
        "deal_value": 50000,
        "days_since_last_contact": 5
    }])
    
    score1 = baseline.score(df)[0]
    score2 = baseline.score(df)[0]
    assert score1 == score2


def test_missing_values(baseline):
    """Missing values follow the Phase 2 contract (handled mostly outside, but check empty behavior)."""
    # Just checking the baseline can handle an empty dataframe with no key features.
    df = pd.DataFrame([{"lead_id": "1"}])
    score = baseline.score(df)[0]
    assert score == 15  # base_prob of 0.15 * 100


def test_leakage_and_protected_attributes(baseline):
    """Excluded fields and protected attributes cannot affect the baseline."""
    df1 = pd.DataFrame([{
        "demo_requested": 1,
        "deal_value": 50000
    }])
    df2 = pd.DataFrame([{
        "demo_requested": 1,
        "deal_value": 50000,
        "converted": 1,             # leakage
        "closed_date": "2026-10-10",# leakage
        "race": "Unknown",          # protected
        "gender": "Male"            # protected
    }])
    
    assert baseline.score(df1)[0] == baseline.score(df2)[0]


def test_ranking_and_tie_breaking(baseline):
    """Higher score ranks ahead of lower score. Equal scores produce deterministic ordering."""
    df = pd.DataFrame([
        {"demo_requested": 0, "deal_value": 1000, "days_since_last_contact": 5}, # low score
        {"demo_requested": 1, "deal_value": 150000, "days_since_last_contact": 5}, # high score
        {"demo_requested": 1, "deal_value": 50000, "days_since_last_contact": 5} # tied score, lower deal value
    ])
    ids = pd.Series(["L1", "L2", "L3"])
    
    ranked = baseline.rank_leads(df, ids)
    
    # Expected order: L2 (high score + high deal), L3 (high score + low deal), L1 (low score)
    # L2 and L3 actually have different scores now because of deal value buckets!
    # L2 deal_value_gt_100k adds 0.10, L3 deal_value_gt_10k adds 0.05.
    
    assert ranked.iloc[0]["lead_id"] == "L2"
    assert ranked.iloc[1]["lead_id"] == "L3"
    assert ranked.iloc[2]["lead_id"] == "L1"

    # Now let's force an absolute tie to test tie breaking
    df_tie = pd.DataFrame([
        {"demo_requested": 1, "deal_value": 150000},
        {"demo_requested": 1, "deal_value": 150000}
    ])
    ids_tie = pd.Series(["L2", "L1"]) # L1 should come first due to ID ascending
    ranked_tie = baseline.rank_leads(df_tie, ids_tie)
    
    assert ranked_tie.iloc[0]["lead_id"] == "L1"
    assert ranked_tie.iloc[1]["lead_id"] == "L2"


def test_archetypes(baseline):
    """Test the baseline using the project's required archetypes."""
    # 1. Hot lead
    hot_lead = pd.DataFrame([{
        "demo_requested": 1,
        "pricing_page_visit": 1,
        "email_clicked": 5,
        "deal_value": 150000,
        "days_since_last_contact": 2
    }])
    hot_score = baseline.score(hot_lead)[0]
    assert hot_score >= 60

    # 2. Cold lead
    cold_lead = pd.DataFrame([{
        "demo_requested": 0,
        "pricing_page_visit": 0,
        "email_clicked": 0,
        "deal_value": 0,
        "days_since_last_contact": 100
    }])
    cold_score = baseline.score(cold_lead)[0]
    assert cold_score < 15

    # 3. High-value lead
    high_value_lead = pd.DataFrame([{
        "deal_value": 250000,
        "annual_revenue": 5000000
    }])
    hv_score = baseline.score(high_value_lead)[0]
    assert hv_score == 30  # base 15 + deal 10 + rev 5

    # 4. Low engagement / high opportunity value
    low_eng_high_opp = pd.DataFrame([{
        "email_clicked": 0,
        "web_visit": 0,
        "deal_value": 200000,
        "opportunity_stage_Proposal": 1
    }])
    score_le_ho = baseline.score(low_eng_high_opp)[0]
    assert score_le_ho > 15
