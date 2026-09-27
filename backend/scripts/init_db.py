import sys
import os
import pandas as pd
from sqlmodel import Session, SQLModel

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from app.models.lead import Lead
from app.models.feedback import Feedback

def init_db():
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully.")

def seed_db():
    print("Seeding database with raw leads data...")
    try:
        leads_df = pd.read_csv("data/leads.csv")
    except Exception as e:
        print(f"Error loading leads.csv: {e}")
        return
        
    with Session(engine) as session:
        # Check if already seeded
        if session.query(Lead).first():
            print("Database already seeded. Skipping.")
            return

        for _, row in leads_df.iterrows():
            lead = Lead(
                lead_id=str(row["lead_id"]),
                annual_revenue=float(row.get("annual_revenue", 0.0)),
                budget=float(row.get("budget", 0.0)),
                deal_value=float(row.get("deal_value", 0.0)),
                previous_purchase=int(row.get("previous_purchase", 0)),
                industry=row.get("industry"),
                company_size=row.get("company_size"),
                lead_source=row.get("lead_source"),
                opportunity_stage=row.get("opportunity_stage")
            )
            session.add(lead)
        
        session.commit()
        print("Database seeded successfully.")

if __name__ == "__main__":
    init_db()
    seed_db()
