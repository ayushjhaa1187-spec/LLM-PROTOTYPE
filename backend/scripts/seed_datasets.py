import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.services.external_data import ingest_from_url
from app.models.user import User

def seed_datasets():
    db = SessionLocal()
    try:
        # Get the first admin user to own these documents
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            # If no admin, just use the first user
            admin = db.query(User).first()
        
        if not admin:
            print("Error: No users found in database. Register a user first.")
            return

        datasets = [
            {
                "url": "https://data.gov.sg/dataset/government-procurement-via-gebiz/download",
                "filename": "Singapore_Procurement_2024.csv"
            },
            {
                "url": "https://raw.githubusercontent.com/datasets/gdp/master/data/gdp.csv",
                "filename": "Global_GDP_Context.csv"
            }
        ]
        
        for ds in datasets:
            print(f"Ingesting {ds['filename']}...")
            ingest_from_url(ds["url"], ds["filename"], db, admin.id)
            print(f"Finished {ds['filename']}")
            
    finally:
        db.close()

if __name__ == "__main__":
    seed_datasets()
