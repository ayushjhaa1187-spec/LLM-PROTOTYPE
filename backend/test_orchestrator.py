import asyncio
from app.database import SessionLocal
from app.agents.orchestrator import run_pipeline
from app.services.vector_store import add_chunks

def test_enterprise_upload():
    # 1. Simulate an uploaded enterprise document being parsed and chunked.
    # We will just inject it into the local vector_store for testing purposes.
    doc_id = "test_enterprise_doc_1"
    
    chunks = [
        "CONFIDENTIAL CONTRACT AGREEMENT. \n\n1. SCOPE: The Vendor agrees to deliver the proprietary AI models to the US Air Force.",
        "2. LIABILITY: The Vendor's liability shall not exceed $10,000 in any event. The Vendor disclaims all implied warranties.",
        "3. DATA PRIVACY: The Vendor may transfer US personnel data to offshore development centers in non-allied nations for processing."
    ]
    
    metadatas = [
        {"doc_id": doc_id, "source": "Vendor_Contract.pdf", "page": 1, "tags": ["contract", "vendor"]},
        {"doc_id": doc_id, "source": "Vendor_Contract.pdf", "page": 2, "tags": ["contract", "vendor"]},
        {"doc_id": doc_id, "source": "Vendor_Contract.pdf", "page": 3, "tags": ["contract", "vendor"]}
    ]
    
    # Generate mock embeddings since we are simulating an offline test or rate-limited account
    embeddings = [[0.0] * 1536 for _ in chunks]
    add_chunks(doc_id, chunks, metadatas, embeddings)
    
    print(f"Uploaded and vectorized enterprise document: {doc_id}")
    
    # 2. Simulate User Query targeting this document
    query = "Audit this contract for FAR Part 52 compliance issues and data residency risks."
    
    print("Running multi-agent RAG pipeline (Research -> Draft -> Verify -> Red Team -> Contracts -> Compliance)...")
    
    # Provide the document ID to trigger the specialized enterprise analyzer agents
    # Use user_id = 1 (admin)
    result = run_pipeline(query=query, document_ids=[doc_id], user_id=1)
    
    print("\n================== RESULTS ==================")
    print(f"Assistent Core Answer: {result['answer'][:150]}...")
    print(f"Blocked?: {result['is_blocked']} (Reason: {result['blocking_reason']})")
    
    if result.get("contract_analysis"):
        print("\n[+] Contract Analysis Results Generated!")
        print(f"Risks Detected: {len(result['contract_analysis'].get('risks', []))}")
        print(f"Summary: {result['contract_analysis'].get('summary', 'No summary')}")
        
    if result.get("compliance_analysis"):
        print("\n[+] Compliance Analysis Results Generated!")
        print(f"Compliance Score: {result['compliance_analysis'].get('compliance_score')}")
        print(f"Regulations Matched: {len(result['compliance_analysis'].get('applicable_regulations', []))}")
        
    print("=============================================\n")

if __name__ == "__main__":
    test_enterprise_upload()
