import sys
import os
import asyncio

# Ensure app is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.query import QueryRecord
from app.models.audit import AuditLog
from app.models.document_version import DocumentVersion
from app.models.conversation import Conversation, ConversationMessage
from app.services.far_ingestion import ingest_far_part
from app.services.ingestors import ingest_pubmed
from app.services.kaggle_ingestion import KaggleIngestionPipeline

async def run_ingestion():
    db = SessionLocal()
    # Dummy admin ID for ingestion since auth is mocked on CLI
    admin_id = 1
    
    print("--- Starting RAG Dataset Ingestion ---\n")
    
    parts_to_ingest = ["19", "22", "39", "2", "13", "52"]
    for part in parts_to_ingest:
        print(f"[*] Ingesting FAR Part {part}...")
        try:
            res = ingest_far_part(part, db=db, user_id=admin_id)
            print(f"    -> Result: {res}")
        except Exception as e:
            print(f"    -> Error ingesting FAR part {part}: {e}")

    print("\n[*] Validating PubMed Ingestion Logic...")
    try:
        pubmed_docs = ingest_pubmed("FAR compliance acquisition", db=db, user_id=admin_id, limit=2)
        print(f"    -> Result: {len(pubmed_docs)} documents ingested")
    except Exception as e:
        print(f"    -> Error ingesting PubMed: {e}")
        
    print("\n[*] Validating Kaggle Ingestion Logic...")
    try:
        kaggle = KaggleIngestionPipeline(db)
        res = await kaggle.ingest_priority_datasets()
        print(f"    -> Result: {res}")
    except Exception as e:
        print(f"    -> Error in Kaggle pipeline: {e}")

    print("\n--- Ingestion Completed ---")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
