import pandas as pd
from typing import Dict, Any, Tuple

def validate_leads_data(leads: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    results = {"valid": True, "errors": []}
    
    required_cols = [
        "lead_id", "industry", "company_size", "annual_revenue", "budget", 
        "lead_source", "opportunity_stage", "deal_value", "previous_purchase", 
        "days_since_last_contact", "converted"
    ]
    
    # 1. Missing fields
    missing_cols = [c for c in required_cols if c not in leads.columns]
    if missing_cols:
        results["valid"] = False
        results["errors"].append(f"Missing required columns: {missing_cols}")
        
    # 2. Invalid data types / nulls
    if leads["lead_id"].isnull().any():
        results["valid"] = False
        results["errors"].append("Found null values in lead_id")
        
    # 3. Duplicate leads
    if leads["lead_id"].duplicated().any():
        results["valid"] = False
        results["errors"].append("Duplicate lead_ids found")
        
    # 4. Invalid categorical values
    valid_stages = ["New", "Contacted", "Qualified", "Proposal", "Closed Won", "Closed Lost"]
    if not leads["opportunity_stage"].isin(valid_stages).all():
        results["valid"] = False
        results["errors"].append("Invalid opportunity_stage values found")
        
    # 5. Invalid numeric ranges
    if (leads["annual_revenue"] < 0).any():
        results["valid"] = False
        results["errors"].append("Negative annual_revenue found")
        
    # 6. Invalid conversion labels
    if not leads["converted"].isin([0, 1]).all():
        results["valid"] = False
        results["errors"].append("converted label must be 0 or 1")
        
    # 7. Check for sensitive attributes
    sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
    found_sensitive = [c for c in sensitive_attrs if c in leads.columns]
    if found_sensitive:
        results["valid"] = False
        results["errors"].append(f"Sensitive attributes found: {found_sensitive}")
        
    return results["valid"], results

def validate_interactions_data(interactions: pd.DataFrame, leads: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
    results = {"valid": True, "errors": []}
    
    required_cols = ["lead_id", "interaction_type", "interaction_date"]
    missing_cols = [c for c in required_cols if c not in interactions.columns]
    if missing_cols:
        results["valid"] = False
        results["errors"].append(f"Missing required columns: {missing_cols}")
        
    # Check if lead_ids in interactions exist in leads
    missing_leads = set(interactions["lead_id"]) - set(leads["lead_id"])
    if missing_leads:
        results["valid"] = False
        results["errors"].append(f"Found interactions for {len(missing_leads)} non-existent leads")
        
    return results["valid"], results
