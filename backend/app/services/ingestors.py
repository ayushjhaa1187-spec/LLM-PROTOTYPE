import os
import shutil
from pathlib import Path
from sec_edgar_downloader import Downloader
from datasets import load_dataset
from sqlalchemy.orm import Session
from app.models.document import Document, ProcessingStatus, AccessLevel
from app.services.external_data import process_sec_10k
from app.config import settings
import uuid
import json
import requests
 

def ingest_sec_10k(ticker: str, db: Session, user_id: str, limit: int = 1):
    """Downloads and ingests latext 10-K filings for a given stock ticker."""
    dl = Downloader(settings.APP_NAME, "admin@example.com", settings.UPLOAD_DIR)
    
    # Download latest 10-K
    dl.get("10-K", ticker, after="2023-01-01", limit=limit)
    
    # SEC Downloader creates a nested structure: uploads/sec-edgar-filings/TICKER/10-K/...
    base_path = Path(settings.UPLOAD_DIR) / "sec-edgar-filings" / ticker / "10-K"
    
    ingested_docs = []
    
    if not base_path.exists():
        return []

    for filing_dir in base_path.iterdir():
        full_text_path = filing_dir / "full-submission.txt"
        if full_text_path.exists():
            # Create a localized copy in our uploads root for the DB record
            safe_filename = f"SEC_10K_{ticker}_{filing_dir.name}.txt"
            target_path = Path(settings.UPLOAD_DIR) / safe_filename
            shutil.copy(full_text_path, target_path)
            
            doc = Document(
                filename=f"SEC 10-K: {ticker} ({filing_dir.name})",
                file_path=str(target_path),
                file_type="txt",
                file_size=target_path.stat().st_size,
                status=ProcessingStatus.UPLOADED,
                access_level=AccessLevel.PUBLIC,
                tags=["sec-edgar", "compliance", ticker.upper()],
                owner_id=user_id,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Use the specialized SEC 10-K processor we built earlier
            process_sec_10k(doc.id, db)
            ingested_docs.append(doc)
            
    return ingested_docs

def ingest_hf_dataset(dataset_name: str, config_name: str = None, split: str = "train", limit: int = 100, db: Session = None, user_id: str = None):
    """Loads a dataset from Hugging Face and ingests a sample into the vector store."""
    doc = None
    try:
        ds = load_dataset(dataset_name, config_name, split=split, streaming=True)
        
        all_chunks = []
        all_metadatas = []
        
        # Create a Virtual Document for this HF dataset subset
        doc = Document(
            filename=f"HF Dataset: {dataset_name}",
            file_path=f"hf://{dataset_name}",
            file_type="hf_dataset",
            file_size=0,
            status=ProcessingStatus.PROCESSING,
            access_level=AccessLevel.PUBLIC,
            tags=["huggingface", "external"],
            owner_id=user_id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        count = 0
        for i, row in enumerate(ds):
            if count >= limit:
                break
            
            # Try to find a text field
            text = row.get("text") or row.get("content") or row.get("body") or str(row)
            
            all_chunks.append(text)
            all_metadatas.append({
                "doc_id": doc.id,
                "source": dataset_name,
                "page": (i // 5) + 1,
                "chunk_index": i,
                "file_type": "hf_row",
            })
            count += 1
            
        if not all_chunks:
            doc.status = ProcessingStatus.FAILED
            doc.error_message = "No data found in dataset"
            db.commit()
            return None

        # Generate embeddings and store
        from app.services.document_processor import _generate_embeddings
        from app.services import vector_store
        
        embeddings = _generate_embeddings(all_chunks)
        vector_store.add_chunks(doc_id=doc.id, chunks=all_chunks, metadatas=all_metadatas, embeddings=embeddings)
        
        doc.status = ProcessingStatus.COMPLETED
        doc.chunk_count = len(all_chunks)
        db.commit()
        
        return doc
    except Exception as e:
        if doc:
            doc.status = ProcessingStatus.FAILED
            doc.error_message = str(e)
            db.commit()
        print(f"HF Ingestion failed: {e}")
        return None

def ingest_kaggle_dataset(dataset_slug: str, db: Session, user_id: str, file_pattern: str = "*.csv", limit_rows: int = 100):
    """Downloads a dataset from Kaggle and ingests it."""
    from kaggle.api.kaggle_api_extended import KaggleApi
    try:
        api = KaggleApi()
        api.authenticate()
        
        # Create a temp dir for download
        download_path = Path(settings.UPLOAD_DIR) / "kaggle" / dataset_slug.replace("/", "_")
        download_path.mkdir(parents=True, exist_ok=True)
        
        # Download files
        api.dataset_download_files(dataset_slug, path=str(download_path), unzip=True)
        
        ingested_docs = []
        # Find matching files
        for file in download_path.glob(file_pattern):
            doc = Document(
                filename=f"Kaggle: {dataset_slug} - {file.name}",
                file_path=str(file),
                file_type=file.suffix[1:],
                file_size=file.stat().st_size,
                status=ProcessingStatus.UPLOADED,
                access_level=AccessLevel.PUBLIC,
                tags=["kaggle", "external", dataset_slug.split("/")[0]],
                owner_id=user_id,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            from app.services.document_processor import process_document
            process_document(doc.id, db)
            ingested_docs.append(doc)
            
        return ingested_docs
    except Exception as e:
        print(f"Kaggle Ingestion failed: {e}")
        return []

def ingest_pubmed(query: str, db: Session, user_id: str, limit: int = 5):
    """Ingests scientific papers from PubMed via the NCBI E-utilities API."""
    import time
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    try:
        # 1. Search for IDs
        search_res = requests.get(f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmode=json&retmax={limit}")
        ids = search_res.json().get("esearchresult", {}).get("idlist", [])
        
        if not ids:
            return []
            
        # 2. Fetch details (Abstracts)
        id_str = ",".join(ids)
        fetch_res = requests.get(f"{base_url}efetch.fcgi?db=pubmed&id={id_str}&retmode=xml")
        
        # Parse XML (simplified usage of BeautifulSoup for PubMed XML)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(fetch_res.content, "xml")
        articles = soup.find_all("PubmedArticle")
        
        ingested_docs = []
        for article in articles:
            title = article.find("ArticleTitle").text if article.find("ArticleTitle") else "PubMed Article"
            abstract = article.find("AbstractText").text if article.find("AbstractText") else "No abstract available."
            pmid = article.find("PMID").text if article.find("PMID") else "unknown"
            
            filename = f"PubMed_{pmid}.txt"
            file_path = os.path.join(settings.UPLOAD_DIR, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"TITLE: {title}\n\nABSTRACT: {abstract}")
                
            doc = Document(
                filename=f"PubMed: {title[:50]}...",
                file_path=file_path,
                file_type="txt",
                file_size=len(abstract),
                status=ProcessingStatus.UPLOADED,
                access_level=AccessLevel.PUBLIC,
                tags=["pubmed", "scientific", "medical"],
                owner_id=user_id,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            from app.services.document_processor import process_document
            process_document(doc.id, db)
            ingested_docs.append(doc)
            
        return ingested_docs
    except Exception as e:
        print(f"PubMed Ingestion failed: {e}")
        return []

def ingest_specialized_llm_data(platform: str, db: Session, user_id: str):
    """Router for specialized platforms like Cosmopedia, FineWeb, or The Stack."""
    platforms = {
        "fineweb": ("HuggingFaceFW/fineweb", "sample-10BT"),
        "cosmopedia": ("HuggingFaceTB/cosmopedia", "auto_math_text"),
        "the_stack": ("bigcode/the-stack", "python"),
        "common_corpus": ("openlm-research/common-corpus", None),
    }
    
    if platform not in platforms:
        raise ValueError(f"Unsupported specialized platform: {platform}")
        
    repo, config = platforms[platform]
    return ingest_hf_dataset(repo, config_name=config, limit=100, db=db, user_id=user_id)

def ingest_regulatory_frameworks(region: str, db: Session, user_id: str):
    """Downloads and ingests official regulatory frameworks based on region."""
    frameworks = {
        "EU": [
            {"name": "GDPR (General Data Protection Regulation)", "url": "https://gdpr-info.eu/art-1-gdpr/", "tags": ["privacy", "eu", "compliance"]},
            {"name": "EU AI Act", "url": "https://artificialintelligenceact.eu/the-act/", "tags": ["ai", "eu", "ethics"]}
        ],
        "US": [
            {"name": "CCPA (California Consumer Privacy Act)", "url": "https://oag.ca.gov/privacy/ccpa", "tags": ["privacy", "us", "california"]},
            {"name": "HIPAA (Health Insurance Portability and Accountability Act)", "url": "https://www.hhs.gov/hipaa/index.html", "tags": ["health", "us", "privacy"]}
        ]
    }
    
    if region not in frameworks:
        raise ValueError(f"No frameworks mapped for region: {region}")
        
    from app.services.external_data import ingest_from_url
    results = []
    for fw in frameworks[region]:
        doc = ingest_from_url(fw["url"], f"{fw['name'].replace(' ', '_')}.txt", db, user_id)
        if doc:
            # Add specific tags
            doc.tags = list(set((doc.tags or []) + fw["tags"]))
            db.commit()
            results.append(doc)
    return results

def ingest_courtlistener(query: str, db: Session, user_id: str, limit: int = 5):
    """Searches CourtListener for case law and ingests the top results."""
    import requests
    from bs4 import BeautifulSoup
    
    headers = {}
    if settings.COURTLISTENER_API_KEY:
        headers["Authorization"] = f"Token {settings.COURTLISTENER_API_KEY}"
        
    try:
        # Search for opinions
        search_url = f"https://www.courtlistener.com/api/rest/v4/search/?type=o&q={query}"
        res = requests.get(search_url, headers=headers)
        res.raise_for_status()
        data = res.json()
        
        results = data.get("results", [])[:limit]
        ingested_docs = []
        
        for item in results:
            # item has 'absolute_url', 'caseName', 'court', 'id'
            # We need to get the full opinion text
            opinion_id = item.get("id")
            if not opinion_id: continue
            
            # Fetch full opinion
            op_res = requests.get(f"https://www.courtlistener.com/api/rest/v4/opinions/{opinion_id}/", headers=headers)
            if not op_res.ok: continue
            
            op_data = op_res.json()
            # Opinions can be in 'html', 'html_with_citations', or 'plain_text'
            raw_content = op_data.get("plain_text") or op_data.get("html_with_citations") or op_data.get("html") or ""
            
            if not raw_content: continue
            
            # Clean HTML if necessary
            if "<" in raw_content and ">" in raw_content:
                soup = BeautifulSoup(raw_content, "html.parser")
                clean_text = soup.get_text(separator="\n")
            else:
                clean_text = raw_content
                
            filename = f"CourtListener_{opinion_id}_{item.get('caseName', 'Unknown')[:50]}"
            file_path = os.path.join(settings.UPLOAD_DIR, f"{filename}.txt")
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(clean_text)
                
            doc = Document(
                filename=item.get('caseName', 'Legal Opinion'),
                file_path=file_path,
                file_type="txt",
                file_size=len(clean_text),
                status=ProcessingStatus.UPLOADED,
                access_level=AccessLevel.PUBLIC,
                tags=["courtlistener", "caselaw", "legal"],
                owner_id=user_id,
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
            
            # Standard processing
            from app.services.document_processor import process_document
            process_document(doc.id, db)
            ingested_docs.append(doc)
            
        return ingested_docs
    except Exception as e:
        print(f"CourtListener Ingestion failed: {e}")
        return []
