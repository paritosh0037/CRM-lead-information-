import pandas as pd
from app.ml.data_validation import validate_leads_data, validate_interactions_data
from app.ml.data_generation import generate_crm_data

def test_validate_leads_data_valid():
    leads, _ = generate_crm_data(num_leads=100)
    is_valid, results = validate_leads_data(leads)
    assert is_valid is True
    assert len(results["errors"]) == 0

def test_validate_leads_data_missing_col():
    leads, _ = generate_crm_data(num_leads=10)
    leads = leads.drop(columns=["industry"])
    is_valid, results = validate_leads_data(leads)
    assert is_valid is False
    assert any("Missing required columns" in e for e in results["errors"])

def test_validate_leads_data_duplicate_ids():
    leads, _ = generate_crm_data(num_leads=10)
    leads.loc[1, "lead_id"] = leads.loc[0, "lead_id"]
    is_valid, results = validate_leads_data(leads)
    assert is_valid is False
    assert any("Duplicate" in e for e in results["errors"])

def test_validate_interactions_valid():
    leads, ints = generate_crm_data(num_leads=10)
    is_valid, results = validate_interactions_data(ints, leads)
    assert is_valid is True

def test_validate_interactions_invalid_lead():
    leads, ints = generate_crm_data(num_leads=10)
    ints.loc[0, "lead_id"] = "INVALID_ID"
    is_valid, results = validate_interactions_data(ints, leads)
    assert is_valid is False
    assert any("non-existent leads" in e for e in results["errors"])
