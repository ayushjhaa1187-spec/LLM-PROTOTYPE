import asyncio
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, engine, Base
from app.models.user import User
import json

import time

# Create a test document
test_doc_path = "test_contract_agreement.txt"
with open(test_doc_path, "w") as f:
    f.write(f"""
PROPRIETARY ENTERPRISE CONTRACT - ACME CORP
Date: October 1st, 2026
Run ID: {time.time()}

1. SCOPE OF WORK
ACME Corp agrees to provide cloud hosting services to the US Federal Government. All data will be hosted on servers located within the continental United States.

2. LIMITATION OF LIABILITY
ACME Corp's total liability under this agreement shall be strictly limited to the total amount paid by the client in the preceding 12 months, or $50,000, whichever is less. We disclaim all warranties.

3. INDEMNIFICATION
The client agrees to indemnify and hold harmless ACME Corp against any and all claims, including those arising from ACME Corp's own negligence.

4. TERMINATION
This contract may be terminated at will by ACME Corp with 24 hours notice.
""")

def run_test():
    # Make sure we have a user
    db = SessionLocal()
    user = db.query(User).filter(User.full_name == "admin").first()
    if not user:
        user = User(email="admin@example.com", full_name="admin", hashed_password="hashed_password", role="admin")
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # We will bypass auth for the test client by overriding dependency (or just fake a token if needed)
    # Actually, let's just use the TestClient
    client = TestClient(app)
    
    # We might need to mock auth. Let's create an override.
    from app.core.security import get_current_user
    app.dependency_overrides[get_current_user] = lambda: user

    print("--- 1. UPLOADING DOCUMENT ---")
    with open(test_doc_path, "rb") as f:
        response = client.post("/api/v1/documents/upload", files={"file": ("test_contract_agreement.txt", f, "text/plain")})
    
    if response.status_code != 200:
        print(f"Failed to upload: {response.text}")
        return
        
    doc_data = response.json()
    doc_id = doc_data["id"]
    print(f"Uploaded Successfully! Document ID: {doc_id}")
    
    # Let's manually trigger processing if needed, though upload might trigger it in background
    # We'll wait a bit or process it synchronously
    from app.services.document_processor import process_document
    print("--- 2. PROCESSING DOCUMENT (Text Extraction, Chunking, Mock Embedding) ---")
    process_document(str(doc_id), db)
    
    print("--- 3. QUERYING RAG PIPELINE ---")
    query_payload = {
        "query": "Does this contract have any risky indemnification or limitation of liability clauses? Analyze against standard compliance.",
        "document_ids": [doc_id]
    }
    
    chat_resp = client.post("/api/v1/queries/", json=query_payload)
    if chat_resp.status_code == 200:
        res = chat_resp.json()
        print("\n=== SYSTEM ANSWER ===")
        print(res.get("answer"))
        print(f"\nBlocked: {res.get('is_blocked')} - Reason: {res.get('blocking_reason')}")
        
        ca = res.get("contract_analysis")
        if ca:
            print("\n=== CONTRACT RISKS DETECTED ===")
            for risk in ca.get("risks", []):
                print(f"- {risk.get('level', 'N/A').upper()}: {risk.get('clause')} -> {risk.get('reason')}")
                
        comp = res.get("compliance_analysis")
        if comp:
            print("\n=== COMPLIANCE SCORE ===")
            print(f"Score: {comp.get('compliance_score')}")
    else:
        print(f"Query Failed: {chat_resp.text}")

if __name__ == "__main__":
    run_test()
