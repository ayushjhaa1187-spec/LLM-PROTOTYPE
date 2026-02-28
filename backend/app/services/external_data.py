import os
import pandas as pd
import requests
from io import StringIO
from sqlalchemy.orm import Session
from app.models.document import Document, ProcessingStatus, AccessLevel
from app.services import document_processor
from app.config import settings
import uuid

def ingest_from_url(url: str, filename: str, db: Session, user_id: str):
    """Downloads a CSV from a URL and ingests it as a document."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Save to uploads directory
        safe_filename = f"external_{uuid.uuid4().hex[:8]}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as f:
            f.write(response.content)
            
        # Create DB record for the "Virtual Document"
        doc = Document(
            filename=filename,
            file_path=file_path,
            file_type="csv",
            file_size=len(response.content),
            status=ProcessingStatus.UPLOADED,
            access_level=AccessLevel.PUBLIC,
            tags=["external", "dataset"],
            owner_id=user_id,
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # We need a special processing step for CSVs to represent them well in RAG
        # Instead of raw text extraction, we'll convert rows to descriptive strings
        process_csv_dataset(doc.id, db)
        
        return doc
    except Exception as e:
        print(f"Failed to ingest dataset from {url}: {e}")
        return None

def process_csv_dataset(doc_id: str, db: Session):
    """Custom CSV processing: converts rows into readable text chunks."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return

    doc.status = ProcessingStatus.PROCESSING
    db.commit()

    try:
        df = pd.read_csv(doc.file_path)
        # Limit to first 500 rows to keep it manageable
        df = df.head(500)
        
        all_chunks = []
        all_metadatas = []
        
        # Convert each row into a descriptive paragraph
        for i, row in df.iterrows():
            row_dict = row.to_dict()
            row_text = ". ".join([f"{k}: {v}" for k, v in row_dict.items() if pd.notnull(v)])
            
            all_chunks.append(row_text)
            all_metadatas.append({
                "doc_id": doc_id,
                "source": doc.filename,
                "page": (i // 10) + 1, # Mock pages
                "chunk_index": i,
                "file_type": "csv_row",
            })
            
        # Batch Generate Embeddings
        from app.services.document_processor import _generate_embeddings
        embeddings = _generate_embeddings(all_chunks)
        
        # Store in Vector Store
        from app.services import vector_store
        vector_store.add_chunks(
            doc_id=doc_id,
            chunks=all_chunks,
            metadatas=all_metadatas,
            embeddings=embeddings,
        )
        
        doc.status = ProcessingStatus.COMPLETED
        doc.chunk_count = len(all_chunks)
        db.commit()
        
    except Exception as e:
        doc.status = ProcessingStatus.FAILED
        doc.error_message = str(e)
        db.commit()
        print(f"Error processing CSV {doc_id}: {e}")

def process_sec_10k(doc_id: str, db: Session):
    """Specialized processing for SEC 10-K Annual Reports."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return

    doc.status = ProcessingStatus.PROCESSING
    db.commit()

    try:
        with open(doc.file_path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        # Simple section splitter for 10-K common headers (Items 1 through 15)
        import re
        sections = re.split(r'(ITEM\s+\d+[A-Z]?\.)', text, flags=re.IGNORECASE)
        
        all_chunks = []
        all_metadatas = []
        
        current_chunk = ""
        for part in sections:
            if len(current_chunk) + len(part) < 3000: # Slightly larger chunks for SEC
                current_chunk += part
            else:
                if current_chunk.strip():
                    all_chunks.append(current_chunk.strip())
                current_chunk = part
        
        if current_chunk.strip():
            all_chunks.append(current_chunk.strip())

        for i, chunk in enumerate(all_chunks):
            all_metadatas.append({
                "doc_id": doc_id,
                "source": doc.filename,
                "page": (i // 2) + 1,
                "chunk_index": i,
                "file_type": "sec_10k_section",
            })

        from app.services.document_processor import _generate_embeddings
        embeddings = _generate_embeddings(all_chunks)
        
        from app.services import vector_store
        vector_store.add_chunks(doc_id=doc_id, chunks=all_chunks, metadatas=all_metadatas, embeddings=embeddings)
        
        doc.status = ProcessingStatus.COMPLETED
        doc.chunk_count = len(all_chunks)
        db.commit()
    except Exception as e:
        doc.status = ProcessingStatus.FAILED
        doc.error_message = str(e)
        db.commit()
