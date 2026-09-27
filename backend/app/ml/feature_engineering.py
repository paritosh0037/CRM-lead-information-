import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple

def load_data(data_dir: str = "data") -> Tuple[pd.DataFrame, pd.DataFrame]:
    leads = pd.read_csv(f"{data_dir}/leads.csv")
    interactions = pd.read_csv(f"{data_dir}/interactions.csv")
    return leads, interactions

def engineer_features(leads: pd.DataFrame, interactions: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Engineers features from CRM data and returns:
    - features (X): DataFrame of model-ready features
    - target (y): Series of the target variable
    - lead_ids: Series of lead identifiers for tracing
    """
    
    df = leads.copy()
    
    # 1. Behavioral Features from Interactions
    if not interactions.empty:
        # Convert interaction_date to datetime
        interactions['interaction_date'] = pd.to_datetime(interactions['interaction_date'])
        
        # Aggregate interaction counts by type
        interaction_counts = interactions.groupby(['lead_id', 'interaction_type']).size().unstack(fill_value=0)
        
        # Total duration
        total_duration = interactions.groupby('lead_id')['duration_seconds'].sum().rename('total_web_duration')
        
        # Total interactions
        total_interactions = interactions.groupby('lead_id').size().rename('total_interactions')
        
        # Merge back to leads
        df = df.merge(interaction_counts, on='lead_id', how='left')
        df = df.merge(total_duration, on='lead_id', how='left')
        df = df.merge(total_interactions, on='lead_id', how='left')
    
    # Fill missing behavioral features with 0
    behavioral_cols = ['email_opened', 'email_clicked', 'call_made', 'web_visit', 
                       'pricing_page_visit', 'demo_requested', 'total_web_duration', 'total_interactions']
    for col in behavioral_cols:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
        else:
            df[col] = 0
            
    # 2. Extract Target and Identifiers
    target = df['converted'].copy()
    lead_ids = df['lead_id'].copy()
    
    # 3. Categorical Preprocessing (One-Hot Encoding)
    # We drop 'opportunity_stage' values that directly leak the target (Closed Won / Closed Lost)
    # Actually, to prevent leakage, we should treat 'Closed Won' and 'Closed Lost' as missing or drop them from the dummy columns
    
    categorical_cols = ['industry', 'company_size', 'lead_source', 'opportunity_stage']
    df_cat = pd.get_dummies(df[categorical_cols], drop_first=False)
    
    # Target Leakage Prevention: Drop dummy columns that perfectly predict the outcome
    leaky_cols = ['opportunity_stage_Closed Won', 'opportunity_stage_Closed Lost']
    df_cat = df_cat.drop(columns=[col for col in leaky_cols if col in df_cat.columns])
    
    # 4. Numeric Features
    numeric_cols = ['annual_revenue', 'budget', 'deal_value', 'previous_purchase', 'days_since_last_contact']
    df_num = df[numeric_cols].copy()
    
    # Handle missing values in numeric columns (if any) using median
    for col in numeric_cols:
        if df_num[col].isnull().any():
            df_num[col] = df_num[col].fillna(df_num[col].median())
            
    # Combine all features
    features = pd.concat([df_num, df_cat, df[behavioral_cols]], axis=1)
    
    # Drop any remaining missing values or sensitive attributes just in case
    sensitive_attrs = ["race", "religion", "ethnicity", "caste", "gender"]
    features = features.drop(columns=[col for col in sensitive_attrs if col in features.columns])
    
    # Ensure boolean/dummy columns are integers for models
    for col in features.columns:
        if features[col].dtype == bool:
            features[col] = features[col].astype(int)
            
    return features, target, lead_ids

def save_features(features: pd.DataFrame, target: pd.Series, lead_ids: pd.Series, output_dir: str = "data"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save the combined model-ready dataset
    dataset = pd.concat([lead_ids, features, target], axis=1)
    dataset.to_csv(f"{output_dir}/model_ready_features.csv", index=False)

if __name__ == "__main__":
    leads, interactions = load_data("f:/pending project/CRM project/backend/data")
    features, target, lead_ids = engineer_features(leads, interactions)
    save_features(features, target, lead_ids, "f:/pending project/CRM project/backend/data")
    print(f"Engineered {features.shape[1]} features for {features.shape[0]} leads.")
