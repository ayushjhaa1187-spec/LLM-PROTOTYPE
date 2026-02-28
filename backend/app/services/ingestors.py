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
