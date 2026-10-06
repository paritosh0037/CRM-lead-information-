import sys
import os
import pandas as pd
from sqlmodel import Session, SQLModel, select

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from app.models.lead import Lead
from app.models.interaction import Interaction
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.feedback import Feedback

def init_db():
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully.")

def seed_db():
    print("Seeding database with raw leads data...")
    try:
        leads_df = pd.read_csv("data/leads.csv")
        interactions_df = pd.read_csv("data/interactions.csv")
    except Exception as e:
        print(f"Error loading CSV data: {e}")
        return
        
    with Session(engine) as session:
        # Check if already seeded
        if session.exec(select(Lead)).first():
            print("Database already seeded. Skipping.")
            return

        for _, row in leads_df.iterrows():
            lead_id = str(row["lead_id"])
            lead = Lead(
                lead_id=lead_id,
                annual_revenue=float(row.get("annual_revenue", 0.0)),
                budget=float(row.get("budget", 0.0)),
                deal_value=float(row.get("deal_value", 0.0)),
                industry=row.get("industry"),
                company_size=row.get("company_size"),
                lead_source=row.get("lead_source"),
                opportunity_stage=row.get("opportunity_stage"),
                previous_purchase=int(row.get("previous_purchase", 0)),
                days_since_last_contact=int(row.get("days_since_last_contact", 30))
            )
            session.add(lead)
            
        for _, row in interactions_df.iterrows():
            inter = Interaction(
                lead_id=str(row["lead_id"]),
                interaction_type=row["interaction_type"],
                duration_seconds=int(row.get("duration_seconds", 0)) if not pd.isna(row.get("duration_seconds")) else 0,
            )
            session.add(inter)
        
        session.commit()
        print("Database seeded with normalized CRM and Interaction records successfully.")

if __name__ == "__main__":
    init_db()
    seed_db()
