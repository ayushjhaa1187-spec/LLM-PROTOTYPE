"""Document management API routes: upload, list, status, detail."""

import os
import shutil
import threading
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, SessionLocal
from app.models.document import Document, ProcessingStatus, AccessLevel
from app.models.audit import AuditLog
from app.models.user import User
from app.services import document_processor
from app.utils.security import get_current_user
from app.utils.rate_limiter import limiter

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def _doc_to_dict(doc: Document) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status.value if hasattr(doc.status, "value") else doc.status,
        "chunk_count": doc.chunk_count,
        "access_level": doc.access_level.value if hasattr(doc.access_level, "value") else doc.access_level,
        "tags": doc.tags or [],
        "error_message": doc.error_message,
        "owner_id": doc.owner_id,
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
    }


def _process_in_background(doc_id: str):
    """Process a document in a background thread using a fresh DB session."""
    db = SessionLocal()
    try:
        document_processor.process_document(doc_id, db)
    finally:
        db.close()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    tags: str = Form(""),
    access_level: str = Form("public"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a document file for processing."""
    # Validate file extension
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate file size (max 50MB)
    contents = await file.read()
    if len(contents) > 50 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 50MB limit",
        )

    # Save file to disk
    safe_filename = f"{os.urandom(8).hex()}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    # Parse tags
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    # Map access level
    access = AccessLevel.PUBLIC
    if access_level == "private":
        access = AccessLevel.PRIVATE
    elif access_level == "admin_only":
        access = AccessLevel.ADMIN_ONLY

    # Create DB record
    doc = Document(
        filename=file.filename or "unnamed",
        file_path=file_path,
        file_type=ext.lstrip("."),
        file_size=len(contents),
        status=ProcessingStatus.UPLOADED,
        access_level=access,
        tags=tag_list,
        owner_id=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="UPLOAD_DOCUMENT",
        resource=doc.id,
        detail=f"Uploaded {file.filename} ({len(contents)} bytes)",
    ))
    db.commit()

    # Start processing in background thread
    thread = threading.Thread(target=_process_in_background, args=(doc.id,))
    thread.start()

    return _doc_to_dict(doc)


@router.get("")
def list_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List documents accessible to the current user."""
    query = db.query(Document)

    # Viewers/Analysts only see public docs and their own private docs
    if current_user.role.value != "admin":
        query = query.filter(
            (Document.access_level == AccessLevel.PUBLIC) |
            (Document.owner_id == current_user.id)
        )

    docs = query.order_by(Document.created_at.desc()).all()
    return [_doc_to_dict(d) for d in docs]


@router.get("/status")
def document_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get processing status for all documents."""
    query = db.query(Document)
    if current_user.role.value != "admin":
        query = query.filter(
            (Document.access_level == AccessLevel.PUBLIC) |
            (Document.owner_id == current_user.id)
        )
    docs = query.order_by(Document.created_at.desc()).all()
    return [_doc_to_dict(d) for d in docs]


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single document's details."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Access check
    if current_user.role.value != "admin":
        if doc.access_level == AccessLevel.ADMIN_ONLY:
            raise HTTPException(status_code=403, detail="Access denied")
        if doc.access_level == AccessLevel.PRIVATE and doc.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return _doc_to_dict(doc)

@router.get("/{doc_id}/chunks")
def get_document_chunks(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get actual vectorized chunks for a document."""
    from app.services import vector_store

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Access check
    if current_user.role.value != "admin":
        if doc.access_level == AccessLevel.ADMIN_ONLY:
            raise HTTPException(status_code=403, detail="Access denied")
        if doc.access_level == AccessLevel.PRIVATE and doc.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Fetch chunks directly from vector store manually
    # The vector_store API only has search, we can search without a real embedding if we implement a fetch
    # To bypass missing API, we'll read vector_store underlying dict
    store = vector_store._load_store()
    
    chunks = []
    for i, meta in enumerate(store["metadatas"]):
        if meta.get("doc_id") == doc_id:
            chunks.append({
                "id": store["ids"][i],
                "page": meta.get("page", 1),
                "section": meta.get("source", doc.filename),
                "text": store["documents"][i]
            })
            
    return chunks

@router.delete("/{doc_id}")
def delete_document_route(
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a document and its chunks from the vector store."""
    from app.services import vector_store

    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Access check: only admins or the owner can delete
    if current_user.role.value != "admin" and doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="DELETE_DOCUMENT",
        resource=doc.id,
        detail=f"Deleted {doc.filename}",
    ))
    db.commit()

    # 1. Delete from OS
    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 2. Delete from Vector Store
    vector_store.delete_document(doc.id)

    # 3. Delete from DB
    db.delete(doc)
    db.commit()

    return {"detail": "Document successfully deleted"}
