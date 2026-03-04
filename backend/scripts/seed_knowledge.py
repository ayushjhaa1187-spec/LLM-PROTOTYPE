"""Seed the RAG knowledge base from local text files.

This script reads all .txt files from data/knowledge_base/,
chunks them, generates embeddings, and stores them in the vector store.

Usage:
    cd backend
    python -m scripts.seed_knowledge
"""

import os
import sys
import time

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import SessionLocal, engine, Base
from app.models.document import Document, ProcessingStatus, AccessLevel
from app.models.user import User, UserRole
from app.models.query import QueryRecord

# Ensure tables exist
Base.metadata.create_all(bind=engine)


def get_or_create_system_user(db):
    """Get or create the system user for document ownership."""
    user = db.query(User).filter(User.email == "system@farcopilot.ai").first()
    if not user:
        user = User(
            email="system@farcopilot.ai",
            hashed_password="api-key-auth-no-password",
            full_name="System User",
            role=UserRole.ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def seed_knowledge_base():
    """Main seeding function."""
    kb_dir = settings.KNOWLEDGE_BASE_DIR
    
    if not os.path.exists(kb_dir):
        print(f"[ERROR] Knowledge base directory not found: {kb_dir}")
        return
    
    txt_files = [f for f in os.listdir(kb_dir) if f.endswith(".txt")]
    if not txt_files:
        print(f"[ERROR] No .txt files found in {kb_dir}")
        return
    
    print(f"\n{'='*60}")
    print(f"  FAR Copilot - Knowledge Base Seeder")
    print(f"  Found {len(txt_files)} knowledge base files")
    print(f"{'='*60}\n")
    
    db = SessionLocal()
    try:
        system_user = get_or_create_system_user(db)
        
        for i, filename in enumerate(sorted(txt_files), 1):
            filepath = os.path.join(kb_dir, filename)
            print(f"[{i}/{len(txt_files)}] Processing: {filename}")
            
            # Check if already ingested
            existing = db.query(Document).filter(
                Document.filename == filename,
                Document.status == ProcessingStatus.COMPLETED,
            ).first()
            
            if existing:
                print(f"  [SKIP] Already ingested ({existing.chunk_count} chunks). Skipping.")
                continue
            
            # Read file content
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()
            
            if not content:
                print(f"  [WARN] Empty file, skipping.")
                continue
            
            file_size = os.path.getsize(filepath)
            
            # Create or update document record
            doc = db.query(Document).filter(Document.filename == filename).first()
            if not doc:
                doc = Document(
                    filename=filename,
                    file_path=filepath,
                    file_type="txt",
                    file_size=file_size,
                    status=ProcessingStatus.UPLOADED,
                    access_level=AccessLevel.PUBLIC,
                    tags=["knowledge-base", "pre-loaded"],
                    owner_id=system_user.id,
                )
                db.add(doc)
                db.commit()
                db.refresh(doc)
            
            # Process: chunk + embed + store
            try:
                _process_text_content(doc.id, content, filename, db)
                print(f"  [OK] Done! ({doc.chunk_count} chunks)")
            except Exception as e:
                print(f"  [ERROR] {e}")
                doc.status = ProcessingStatus.FAILED
                doc.error_message = str(e)
                db.commit()
        
        print(f"\n{'='*60}")
        print(f"  [SUCCESS] Knowledge base seeding complete!")
        
        # Show stats
        from app.services import vector_store
        stats = vector_store.get_collection_stats()
        total_docs = db.query(Document).filter(Document.status == ProcessingStatus.COMPLETED).count()
        print(f"  Total documents: {total_docs}")
        print(f"  Total vector chunks: {stats['total_chunks']}")
        print(f"{'='*60}\n")
        
    finally:
        db.close()


def _process_text_content(doc_id: str, content: str, filename: str, db):
    """Process raw text content: chunk, embed, store."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from app.services import vector_store
    from app.models.document import Document, ProcessingStatus
    
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise ValueError(f"Document {doc_id} not found")
    
    doc.status = ProcessingStatus.PROCESSING
    db.commit()
    
    # Chunk the text
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator=True,
    )
    
    chunks = splitter.split_text(content)
    
    if not chunks:
        raise ValueError("No viable chunks produced from text")
    
    # Generate embeddings
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("sk-your"):
        print(f"  [WARN] No valid OpenAI API key. Storing chunks without embeddings.")
        # Store with zero embeddings (will work for keyword-based retrieval)
        import numpy as np
        embeddings = [list(np.zeros(1536).astype(float)) for _ in chunks]
    else:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        embeddings = []
        batch_size = 100
        for j in range(0, len(chunks), batch_size):
            batch = chunks[j:j + batch_size]
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=batch,
            )
            for item in response.data:
                embeddings.append(item.embedding)
    
    # Build metadata
    metadatas = []
    for idx, chunk in enumerate(chunks):
        metadatas.append({
            "doc_id": doc_id,
            "source": filename,
            "page": 1,
            "chunk_index": idx,
            "file_type": "txt",
        })
    
    # Store in vector DB
    vector_store.add_chunks(
        doc_id=doc_id,
        chunks=chunks,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    
    # Update document status
    doc.status = ProcessingStatus.COMPLETED
    doc.chunk_count = len(chunks)
    doc.error_message = None
    db.commit()


if __name__ == "__main__":
    seed_knowledge_base()
