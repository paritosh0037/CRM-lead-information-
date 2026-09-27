import pandas as pd
from app.ml.feature_engineering import engineer_features, load_data
from app.ml.data_generation import generate_crm_data
import os

def test_feature_engineering_executes():
    leads, ints = generate_crm_data(num_leads=50)
    features, target, lead_ids = engineer_features(leads, ints)
    
    assert len(features) == 50
    assert len(target) == 50
    assert len(lead_ids) == 50
    
    # Ensure target is not in features
    assert "converted" not in features.columns
    
    # Ensure leaky columns are absent
    assert "opportunity_stage_Closed Won" not in features.columns
    assert "opportunity_stage_Closed Lost" not in features.columns

def test_feature_engineering_unique_ids():
    leads, ints = generate_crm_data(num_leads=50)
    _, _, lead_ids = engineer_features(leads, ints)
    assert lead_ids.is_unique

def test_feature_engineering_numeric_types():
    leads, ints = generate_crm_data(num_leads=50)
    features, _, _ = engineer_features(leads, ints)
    
    # All columns should be numeric (int or float)
    for col in features.columns:
        assert pd.api.types.is_numeric_dtype(features[col]), f"Column {col} is not numeric"

def test_feature_engineering_missing_values():
    leads, ints = generate_crm_data(num_leads=50)
    # Introduce some missing values
    leads.loc[0, "annual_revenue"] = None
    features, _, _ = engineer_features(leads, ints)
    
    assert not features.isnull().any().any()

def test_feature_engineering_no_sensitive_attrs():
    leads, ints = generate_crm_data(num_leads=50)
    leads["gender"] = "M"
    features, _, _ = engineer_features(leads, ints)
    
    sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
    for attr in sensitive_attrs:
        assert attr not in features.columns

def test_feature_engineering_reproducibility():
    leads, ints = generate_crm_data(num_leads=50)
    features1, target1, lead_ids1 = engineer_features(leads, ints)
    features2, target2, lead_ids2 = engineer_features(leads, ints)
    
    assert features1.equals(features2)
    assert target1.equals(target2)
    assert lead_ids1.equals(lead_ids2)
