import pandas as pd
import numpy as np
from typing import Tuple
from pathlib import Path
from datetime import datetime, timedelta

def generate_crm_data(num_leads: int = 3000, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates synthetic CRM data with realistic behavioral sequences.
    Ensures reproducibility using a random seed.
    """
    np.random.seed(seed)
    
    # Lead profiles
    lead_ids = [f"L{i:05d}" for i in range(1, num_leads + 1)]
    
    industries = ["Technology", "Healthcare", "Finance", "Retail", "Manufacturing"]
    company_sizes = ["1-50", "51-200", "201-1000", "1000+"]
    lead_sources = ["Organic Search", "Paid Ads", "Referral", "Outbound", "Event"]
    stages = ["New", "Contacted", "Qualified", "Proposal", "Closed Won", "Closed Lost"]
    
    leads = pd.DataFrame({
        "lead_id": lead_ids,
        "industry": np.random.choice(industries, num_leads),
        "company_size": np.random.choice(company_sizes, num_leads),
        "annual_revenue": np.random.uniform(100000, 50000000, num_leads).round(2),
        "budget": np.random.uniform(5000, 500000, num_leads).round(2),
        "lead_source": np.random.choice(lead_sources, num_leads),
        "opportunity_stage": np.random.choice(stages, num_leads, p=[0.2, 0.2, 0.2, 0.2, 0.1, 0.1]),
        "deal_value": np.random.uniform(1000, 100000, num_leads).round(2),
        "previous_purchase": np.random.choice([0, 1], num_leads, p=[0.8, 0.2]),
        "days_since_last_contact": np.random.randint(0, 365, num_leads)
    })
    
    # Target label: converted
    # We create a logic where some fields correlate with conversion
    # E.g., 'Closed Won' is always converted=1. Others based on some probability
    leads["converted"] = 0
    leads.loc[leads["opportunity_stage"] == "Closed Won", "converted"] = 1
    
    # Add some correlation with interactions for other stages
    
    # Interactions
    interactions = []
    interaction_types = ["email_opened", "email_clicked", "call_made", "web_visit", "pricing_page_visit", "demo_requested"]
    
    # Use a fixed reference date for reproducibility
    end_date = datetime(2024, 1, 1)
    
    for lead_id in lead_ids:
        num_interactions = np.random.randint(0, 20)
        
        for _ in range(num_interactions):
            i_type = np.random.choice(interaction_types, p=[0.3, 0.2, 0.1, 0.2, 0.1, 0.1])
            days_ago = np.random.randint(0, 365)
            i_date = end_date - timedelta(days=days_ago)
            
            interactions.append({
                "lead_id": lead_id,
                "interaction_type": i_type,
                "interaction_date": i_date.isoformat(),
                "duration_seconds": np.random.randint(10, 300) if i_type in ["web_visit", "pricing_page_visit", "call_made"] else 0
            })
            
    interactions_df = pd.DataFrame(interactions)
    
    # Post-process target based on interactions
    if not interactions_df.empty:
        interaction_counts = interactions_df.groupby(["lead_id", "interaction_type"]).size().unstack(fill_value=0)
        
        leads = leads.merge(interaction_counts, on="lead_id", how="left").fillna(0)
        
        # Simple logical conversion correlation
        prob = 0.05 + (leads.get("demo_requested", 0) * 0.3) + (leads.get("pricing_page_visit", 0) * 0.1)
        prob = np.clip(prob, 0, 1)
        
        random_probs = np.random.rand(num_leads)
        mask = (random_probs < prob) & (leads["opportunity_stage"] != "Closed Lost")
        leads.loc[mask, "converted"] = 1
        
        # Drop temporary columns for pure raw data structure, they will be re-engineered in ML pipeline
        for col in interaction_types:
            if col in leads.columns:
                leads = leads.drop(columns=[col])

    return leads, interactions_df

def save_dataset(leads: pd.DataFrame, interactions: pd.DataFrame, output_dir: str = "data"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    leads.to_csv(f"{output_dir}/leads.csv", index=False)
    interactions.to_csv(f"{output_dir}/interactions.csv", index=False)

if __name__ == "__main__":
    leads, interactions = generate_crm_data()
    save_dataset(leads, interactions, "f:/pending project/CRM project/backend/data")
    print(f"Generated {len(leads)} leads and {len(interactions)} interactions.")
