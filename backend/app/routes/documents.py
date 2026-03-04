"""Document upload and management routes (SEC-01).

Includes secure file handling, magic byte validation, and audit logging.
"""

import os
import secrets
import hashlib
import magic
from typing import List, Optional
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.core import security
from app.core.audit import AuditLogger
from app.models.document import Document
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    created_at: str


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: security.User = Depends(security.get_current_user)
):
    """Securely upload a document with magic byte validation and SHA-256 hashing."""
    # 1. Filename sanitization
    safe_filename = "".join([c for c in file.filename if c.isalnum() or c in "._-"]).strip()
    if not safe_filename:
        safe_filename = f"upload_{secrets.token_hex(8)}"
        
    # 2. File size validation
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)")
        
    # 3. Magic byte validation (Day 1 SEC-01)
    mime = magic.from_buffer(file_content, mime=True)
    allowed_mimes = [
        "application/pdf", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document", # docx
        "text/plain", 
        "text/xml", 
        "application/xml"
    ]
    if mime not in allowed_mimes:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {mime}")
        
    # 4. SHA-256 for deduplication and integrity
    sha256_hash = hashlib.sha256(file_content).hexdigest()
    if db.query(Document).filter(Document.sha256 == sha256_hash).first():
       raise HTTPException(status_code=400, detail="Document already exists (SHA-256 match)")
       
    # 5. Save file
    file_ext = safe_filename.split(".")[-1] if "." in safe_filename else "txt"
    storage_filename = f"{sha256_hash}.{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, storage_filename)
    
    with open(file_path, "wb") as f:
        f.write(file_content)
        
    # 6. Create DB record
    doc = Document(
        filename=safe_filename,
        file_path=file_path,
        file_type=file_ext,
        file_size=file_size,
        status="uploaded",
        sha256=sha256_hash,
        owner_id=user.id
    )
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # 7. Audit log (SEC-03)
    AuditLogger.log(db, user.id, "UPLOAD", "document", {"id": doc.id, "filename": doc.filename}, request.client.host)
    
    # Trigger background processing (Placeholder for now)
    # process_document_task.delay(doc.id)
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "created_at": doc.created_at.isoformat()
    }


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    db: Session = Depends(get_db),
    user: security.User = Depends(security.get_current_user)
):
    """List documents owned by the current user."""
    docs = db.query(Document).filter(Document.owner_id == user.id).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "status": doc.status,
            "created_at": doc.created_at.isoformat()
        } for doc in docs
    ]
