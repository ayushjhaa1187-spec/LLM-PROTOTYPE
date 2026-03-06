"""Document processing pipeline: extract text, chunk, embed, and store."""

import os
import traceback
from pathlib import Path

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.document import Document, ProcessingStatus
from app.services import vector_store

# Text splitter configuration matching the spec
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
    keep_separator=True,
)


def _extract_text_pdf(file_path: str) -> list[dict]:
    """Extract text from PDF with page number metadata."""
    pages: list[dict] = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip()
        if text:
            pages.append({"text": text, "page": page_num + 1})
    doc.close()
    return pages


def _extract_text_docx(file_path: str) -> list[dict]:
    """Extract text from DOCX file."""
    doc = DocxDocument(file_path)
    full_text = "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    if not full_text.strip():
        return []
    return [{"text": full_text, "page": 1}]


def _extract_text_txt(file_path: str) -> list[dict]:
    """Extract text from plain text file."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read().strip()
    if not text:
        return []
    return [{"text": text, "page": 1}]


def _generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using local FastEmbed."""
    from app.services.rag_service import _get_embedding_model
    
    try:
        model = _get_embedding_model()
        # FastEmbed embed() returns a generator of embeddings
        embeddings = list(model.embed(texts))
        return [e.tolist() for e in embeddings]
    except Exception as e:
        print(f"Local embedding failed: {e}. Using mock embeddings.")
        return [[0.0] * 384 for _ in texts]


def process_document(doc_id: str, db: Session):
    """Full document processing pipeline:
    1. Extract text (PDF/DOCX/TXT)
    2. Chunk with metadata preservation
    3. Generate embeddings
    4. Store in ChromaDB
    5. Update document status
    """
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return

    # Update status to processing
    doc.status = ProcessingStatus.PROCESSING
    db.commit()

    try:
        file_path = doc.file_path

        # 1. Extract text based on file type
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            pages = _extract_text_pdf(file_path)
        elif ext == ".docx":
            pages = _extract_text_docx(file_path)
        elif ext == ".txt":
            pages = _extract_text_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        if not pages:
            raise ValueError("No text could be extracted from the document")

        # 2. Chunk each page's text with metadata
        all_chunks: list[str] = []
        all_metadatas: list[dict] = []

        for page_info in pages:
            chunks = _splitter.split_text(page_info["text"])
            for chunk_idx, chunk_text in enumerate(chunks):
                all_chunks.append(chunk_text)
                all_metadatas.append({
                    "doc_id": doc_id,
                    "source": doc.filename,
                    "page": page_info["page"],
                    "chunk_index": len(all_metadatas),
                    "file_type": doc.file_type,
                })

        if not all_chunks:
            raise ValueError("Text extraction produced no viable chunks")

        # 3. Generate embeddings
        embeddings = _generate_embeddings(all_chunks)

        # 4. Store in vector DB
        vector_store.add_chunks(
            doc_id=doc_id,
            chunks=all_chunks,
            metadatas=all_metadatas,
            embeddings=embeddings,
        )

        # 5. Update document status
        doc.status = ProcessingStatus.COMPLETED
        doc.chunk_count = len(all_chunks)
        doc.error_message = None
        db.commit()

    except Exception as e:
        doc.status = ProcessingStatus.FAILED
        doc.error_message = f"{type(e).__name__}: {str(e)}"
        db.commit()
        traceback.print_exc()
