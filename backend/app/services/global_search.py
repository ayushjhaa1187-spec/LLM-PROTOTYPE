"""Global Search Service: Orchestrates search across multiple remote legal and financial sources."""

import threading
from app.services import vector_store
from app.services.ingestors import ingest_courtlistener, ingest_sec_10k
from app.models.document import Document
from sqlalchemy.orm import Session
import concurrent.futures

def global_search(query: str, db: Session, user_id: str):
    """
    Executes a parallel search across:
    1. Local Vector Store (Fast)
    2. CourtListener Opinions (API)
    3. SEC 10-K Filings (API/Download)
    
    This is intended to be a 'comprehensive' discovery mode.
    """
    results = {
        "local": [],
        "courtlistener": [],
        "sec": [],
        "status": "partial"
    }

    # 1. Local Search (Synchronous/Blocking)
    results["local"] = vector_store.search(query, k=5)

    # 2. Parallel Remote 'Pulling' 
    # Note: For Global Search, we don't just search, we INGEST the findings so they are permanently available.
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        cl_future = executor.submit(ingest_courtlistener, query, db, user_id, limit=2)
        
        # For SEC, we try to detect if the query has a ticker. If not, we skip the raw pull.
        import re
        ticker_match = re.search(r'\$?([A-Z]{1,5})', query.upper())
        sec_future = None
        if ticker_match:
            ticker = ticker_match.group(1)
            sec_future = executor.submit(ingest_sec_10k, ticker, db, user_id, limit=1)

    try:
        if cl_future:
            results["courtlistener"] = [doc.filename for doc in cl_future.result()]
        if sec_future:
            results["sec"] = [doc.filename for doc in sec_future.result()]
    except Exception as e:
        print(f"Global Search Remote Error: {e}")

    results["status"] = "completed"
    return results
