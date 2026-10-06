import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional
from datetime import datetime

def load_data(data_dir: str = "data") -> Tuple[pd.DataFrame, pd.DataFrame]:
    leads = pd.read_csv(f"{data_dir}/leads.csv")
    interactions = pd.read_csv(f"{data_dir}/interactions.csv")
    return leads, interactions

def validate_lead_data(df: pd.DataFrame) -> pd.DataFrame:
    """Applies the invalid data contract rules to CRM fields."""
    # Negative value validation (coerce to 0.0 or NaN as per domain rules)
    for col in ['budget', 'annual_revenue', 'deal_value']:
        if col in df.columns:
            df.loc[df[col] < 0, col] = 0.0
            
    # Days since last contact cannot be negative
    if 'days_since_last_contact' in df.columns:
        df.loc[df['days_since_last_contact'] < 0, 'days_since_last_contact'] = np.nan
        
    return df

def engineer_features(
    leads: pd.DataFrame, 
    interactions: pd.DataFrame,
    prediction_timestamp: Optional[datetime] = None
) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Engineers features from CRM data following the Phase 2 Feature Contract.
    - filters historical interactions by `prediction_timestamp`
    - prevents target leakage
    - handles missing and invalid values
    - drops protected/sensitive attributes
    """
    
    df = leads.copy()
    
    # 0. Exclude Protected/Sensitive Attributes
    sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
    df = df.drop(columns=[col for col in sensitive_attrs if col in df.columns])
    
    # 1. Validation Contract
    df = validate_lead_data(df)
    
    # 2. Historical Interaction Aggregation (Prediction-Point Safety)
    if not interactions.empty:
        interactions['interaction_date'] = pd.to_datetime(interactions['interaction_date'], utc=True)
        
        # Enforce prediction timestamp filtering
        if prediction_timestamp is not None:
            # Ensure prediction_timestamp is timezone-aware for comparison
            if prediction_timestamp.tzinfo is None:
                prediction_timestamp = prediction_timestamp.replace(tzinfo=pd.Timestamp.utcnow().tz)
            
            # Filter out future interactions to prevent leakage
            valid_interactions = interactions[interactions['interaction_date'] <= prediction_timestamp].copy()
        else:
            valid_interactions = interactions.copy()
            
        # Aggregate interaction counts by type
        interaction_counts = valid_interactions.groupby(['lead_id', 'interaction_type']).size().unstack(fill_value=0)
        
        # Total duration
        if 'duration_seconds' in valid_interactions.columns:
            total_duration = valid_interactions.groupby('lead_id')['duration_seconds'].sum().rename('total_web_duration')
        else:
            total_duration = valid_interactions.groupby('lead_id').apply(lambda x: 0).rename('total_web_duration')
            
        # Total interactions
        total_interactions = valid_interactions.groupby('lead_id').size().rename('total_interactions')
        
        # Merge back to leads
        df = df.merge(interaction_counts, on='lead_id', how='left')
        df = df.merge(total_duration, on='lead_id', how='left')
        df = df.merge(total_interactions, on='lead_id', how='left')
    
    # Missing Data Contract for Behavioral Features
    # Missing interactions explicitly mean 0 occurrences
    behavioral_cols = ['email_opened', 'email_clicked', 'call_made', 'web_visit', 
                       'pricing_page_visit', 'demo_requested', 'total_web_duration', 'total_interactions']
    for col in behavioral_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            df[col] = 0
            
    # 3. Extract Target and Identifiers
    # The 'converted' field is the explicit target outcome.
    if 'converted' in df.columns:
        target = df['converted'].copy()
    else:
        target = pd.Series(0, index=df.index, name='converted')
        
    lead_ids = df['lead_id'].copy()
    
    # 4. Leakage Audit & Prevention
    # Drop the target and manually entered post-outcome fields from feature space
    leakage_risks = ['converted', 'closed_date', 'won_reason', 'lost_reason']
    df = df.drop(columns=[col for col in leakage_risks if col in df.columns])
    
    # Map post-conversion opportunity stages to 'Unknown' to prevent leakage
    if 'opportunity_stage' in df.columns:
        df['opportunity_stage'] = df['opportunity_stage'].replace(
            ['Closed Won', 'Closed Lost', 'Closed'], 'Unknown'
        )
    
    # 5. Categorical Preprocessing (One-Hot Encoding)
    categorical_cols = ['industry', 'company_size', 'lead_source', 'opportunity_stage']
    existing_cat_cols = [col for col in categorical_cols if col in df.columns]
    
    if existing_cat_cols:
        # Missing values in categories become "Unknown"
        df[existing_cat_cols] = df[existing_cat_cols].fillna("Unknown")
        df_cat = pd.get_dummies(df[existing_cat_cols], drop_first=False)
    else:
        df_cat = pd.DataFrame(index=df.index)
    
    # 6. Numeric Features and Missing Data Contract
    numeric_cols = ['annual_revenue', 'budget', 'deal_value', 'previous_purchase', 'days_since_last_contact']
    existing_num_cols = [col for col in numeric_cols if col in df.columns]
    df_num = df[existing_num_cols].copy()
    
    # Missing Value Contract:
    # budget, revenue, deal_value -> 0.0 (Assume no budget/revenue/deal value known)
    for col in ['budget', 'annual_revenue', 'deal_value', 'previous_purchase']:
        if col in df_num.columns:
            df_num[col] = df_num[col].fillna(0.0)
            
    # days_since_last_contact -> 999 (Indicates stale/unknown contact history)
    if 'days_since_last_contact' in df_num.columns:
        df_num['days_since_last_contact'] = df_num['days_since_last_contact'].fillna(999.0)
            
    # 7. Combine all features
    features = pd.concat([df_num, df_cat, df[behavioral_cols]], axis=1)
    
    # Ensure boolean columns from get_dummies are integers
    for col in features.columns:
        if features[col].dtype == bool:
            features[col] = features[col].astype(int)
            
    return features, target, lead_ids

def save_features(features: pd.DataFrame, target: pd.Series, lead_ids: pd.Series, output_dir: str = "data"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    dataset = pd.concat([lead_ids, features, target], axis=1)
    dataset.to_csv(f"{output_dir}/model_ready_features.csv", index=False)

if __name__ == "__main__":
    leads, interactions = load_data("f:/pending project/CRM project/backend/data")
    features, target, lead_ids = engineer_features(leads, interactions)
    save_features(features, target, lead_ids, "f:/pending project/CRM project/backend/data")
    print(f"Engineered {features.shape[1]} features for {features.shape[0]} leads.")
