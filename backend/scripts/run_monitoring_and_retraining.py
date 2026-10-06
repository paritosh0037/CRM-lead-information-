import os
import sys
import json
import shutil
from pathlib import Path
import pandas as pd
import datetime

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.monitoring import ModelMonitor, RetrainingEngine
from app.ml.train import run_training_pipeline
from app.services.lead_service import LeadService
from sqlmodel import select
from app.models.lead import Lead

def load_metrics(metrics_path: str) -> dict:
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {}

def run_workflow():
    print(f"[{datetime.datetime.now().isoformat()}] Starting Model Monitoring & Batch Retraining Workflow...")
    
    # 1. Initialize Monitor
    monitor = ModelMonitor(
        numerical_drift_threshold=0.1,
        categorical_drift_threshold=0.15,
        auc_degradation_threshold=0.65,
    )
    
    data_dir = Path("data")
    
    # The reference data (training data) must be loaded from CSV as it is the historical snapshot the model trained on
    reference_path = data_dir / "model_ready_features.csv"
    if not reference_path.exists():
        print("Reference dataset not found. Aborting.")
        return
        
    ref_df = pd.read_csv(reference_path)
    
    # CURRENT CRM Data from Database
    lead_service = LeadService()
    
    with lead_service._get_db_session() as session:
        cur_df = lead_service._build_features_from_db(session)
        # For actual outcome evaluation
        db_leads = session.exec(select(Lead)).all()
        cur_raw_leads = pd.DataFrame([lead.model_dump() for lead in db_leads])
        
    if cur_df.empty:
        print("No current data in database. Aborting.")
        return
        
    # Since reference_df is model_ready_features, categorical columns are One-Hot Encoded.
    num_features = ["annual_revenue", "budget", "deal_value", "total_web_duration", "total_interactions"]
    cat_features = [c for c in ref_df.columns if c.startswith("industry_") or c.startswith("lead_source_")]
    
    ref_preds_path = data_dir / "predictions.csv"
    if not ref_preds_path.exists():
        print("Reference predictions not found. Aborting.")
        return
        
    ref_preds = pd.read_csv(ref_preds_path)
    
    # Run Current Predictions
    # Using existing ML engine to predict
    cur_preds = lead_service.ml_engine.predict_batch(cur_df)
    
    y_true = cur_df["converted"].values if "converted" in cur_df.columns else None
    y_proba = cur_preds["conversion_probability"].values
    
    # 2. Generate Monitoring Report
    print("Generating Monitoring Report...")
    report = monitor.generate_report(
        model_version="v1.0",
        reference_df=ref_df,
        current_df=cur_df,
        numerical_features=num_features,
        categorical_features=cat_features,
        reference_preds=ref_preds,
        current_preds=cur_preds,
        actual_outcomes=y_true,
        predicted_probs=y_proba
    )
    
    report_path = data_dir / "monitoring_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(f"Monitoring Report generated: {report_path}")
    print(f"Retraining Recommendation: {report['retraining_recommendation']} (Severity: {report['severity']})")
    for reason in report["reasons"]:
        print(f" - {reason}")
        
    print("\n--- MONITORING COMPLETE ---")
    print("NO AUTOMATIC RETRAINING: Retraining must be triggered manually based on the recommendation state.")

if __name__ == "__main__":
    run_workflow()
