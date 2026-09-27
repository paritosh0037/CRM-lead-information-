import pandas as pd
from app.ml.data_generation import generate_crm_data

def test_generate_crm_data_reproducibility():
    leads1, ints1 = generate_crm_data(num_leads=100, seed=42)
    leads2, ints2 = generate_crm_data(num_leads=100, seed=42)
    
    assert leads1.equals(leads2)
    assert ints1.equals(ints2)

def test_generate_crm_data_size():
    leads, ints = generate_crm_data(num_leads=2500)
    assert len(leads) == 2500
    assert len(ints) >= 0

def test_generate_crm_data_fields():
    leads, _ = generate_crm_data(num_leads=10)
    required_cols = [
        "lead_id", "industry", "company_size", "annual_revenue", "budget", 
        "lead_source", "opportunity_stage", "deal_value", "previous_purchase", 
        "days_since_last_contact", "converted"
    ]
    for col in required_cols:
        assert col in leads.columns
    
    # Ensure sensitive fields are absent
    sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
    for attr in sensitive_attrs:
        assert attr not in leads.columns

def test_generate_crm_data_unique_ids():
    leads, _ = generate_crm_data(num_leads=100)
    assert leads["lead_id"].is_unique
