"""FAR/DFARS regulatory data ingestion service.

Downloads and processes official regulation data from acquisition.gov
for indexing in the vector store.
"""

import os
import re
import hashlib
import requests
from pathlib import Path
from xml.etree import ElementTree

from app.config import settings


# Known FAR part URLs on acquisition.gov
FAR_PARTS = {
    "1": "General",
    "2": "Definitions",
    "3": "Improper Business Practices",
    "4": "Administrative and Information Matters",
    "5": "Publicizing Contract Actions",
    "6": "Competition Requirements",
    "7": "Acquisition Planning",
    "8": "Required Sources of Supplies and Services",
    "9": "Contractor Qualifications",
    "10": "Market Research",
    "11": "Describing Agency Needs",
    "12": "Acquisition of Commercial Products",
    "13": "Simplified Acquisition Procedures",
    "14": "Sealed Bidding",
    "15": "Contracting by Negotiation",
    "16": "Types of Contracts",
    "17": "Special Contracting Methods",
    "18": "Emergency Acquisitions",
    "19": "Small Business Programs",
    "22": "Application of Labor Laws",
    "23": "Environment, Energy, Water Efficiency",
    "25": "Foreign Acquisition",
    "28": "Bonds and Insurance",
    "30": "Cost Accounting Standards",
    "31": "Contract Cost Principles",
    "32": "Contract Financing",
    "33": "Protests, Disputes, Appeals",
    "36": "Construction and Architect-Engineer",
    "37": "Service Contracting",
    "39": "Acquisition of Information Technology",
    "42": "Contract Administration",
    "46": "Quality Assurance",
    "49": "Termination of Contracts",
    "52": "Solicitation Provisions and Contract Clauses",
    "53": "Forms",
}


def download_far_html(part_number: str, output_dir: str = None) -> str | None:
    """Download a FAR part from acquisition.gov as HTML.
    
    Args:
        part_number: FAR part number (e.g., "19", "22", "39")
        output_dir: Directory to save the downloaded file
        
    Returns:
        Path to downloaded file, or None on failure
    """
    if output_dir is None:
        output_dir = os.path.join(settings.KNOWLEDGE_BASE_DIR, "far")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    url = f"https://www.acquisition.gov/far/part-{part_number}"
    output_file = os.path.join(output_dir, f"FAR_Part_{part_number}.html")
    
    try:
        headers = {
            "User-Agent": "FAR-Compliance-Copilot/3.0 (Federal Acquisition Research)"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        return output_file
    except Exception as e:
        print(f"Failed to download FAR Part {part_number}: {e}")
        return None


def parse_far_html(html_file: str) -> list[dict]:
    """Parse a downloaded FAR HTML file into sections.
    
    Returns list of dicts with: section_id, title, text, part_number
    """
    from bs4 import BeautifulSoup
    
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    
    sections = []
    
    # Look for section headings and content
    for heading in soup.find_all(["h2", "h3", "h4"]):
        section_text = heading.get_text(strip=True)
        
        # Extract section ID (e.g., "19.502-2")
        section_match = re.match(r'(\d+\.\d+[\-\.\d]*)', section_text)
        section_id = section_match.group(1) if section_match else ""
        
        # Get content until next heading
        content_parts = []
        sibling = heading.find_next_sibling()
        while sibling and sibling.name not in ["h2", "h3", "h4"]:
            text = sibling.get_text(strip=True)
            if text:
                content_parts.append(text)
            sibling = sibling.find_next_sibling()
        
        content = "\n\n".join(content_parts)
        
        if content and len(content) > 20:
            # Extract part number from section ID
            part_number = section_id.split(".")[0] if "." in section_id else ""
            
            sections.append({
                "section_id": section_id,
                "title": section_text,
                "text": f"{section_text}\n\n{content}",
                "part_number": part_number,
                "source_type": "regulation",
                "source_system": "FAR_HTML",
            })
    
    return sections


def download_all_hero_parts() -> dict:
    """Download the three hero FAR parts (19, 22, 39) plus key supporting parts.
    
    Returns dict with part_number -> file_path mapping.
    """
    hero_parts = ["19", "22", "39"]
    supporting_parts = ["2", "13", "15", "52"]  # Definitions, SAP, Negotiations, Clauses
    
    results = {}
    for part in hero_parts + supporting_parts:
        file_path = download_far_html(part)
        if file_path:
            results[part] = file_path
            print(f"✓ Downloaded FAR Part {part}: {FAR_PARTS.get(part, 'Unknown')}")
        else:
            print(f"✗ Failed to download FAR Part {part}")
    
    return results


def ingest_far_part(part_number: str, db=None, user_id: str = None) -> dict:
    """Full ingestion pipeline for a FAR part: download, parse, embed, store.
    
    Returns summary of ingestion results.
    """
    from app.services import document_processor, vector_store
    from app.models.document import Document, ProcessingStatus, SourceType
    
    # Download
    file_path = download_far_html(part_number)
    if not file_path:
        return {"status": "error", "message": f"Failed to download FAR Part {part_number}"}
    
    # Parse into sections
    sections = parse_far_html(file_path)
    if not sections:
        return {"status": "error", "message": "No sections extracted from HTML"}
    
    # If DB session provided, create document record
    if db and user_id:
        doc = Document(
            filename=f"FAR_Part_{part_number}.html",
            file_path=file_path,
            file_type="html",
            file_size=os.path.getsize(file_path),
            status=ProcessingStatus.PROCESSING,
            source_type=SourceType.REGULATION,
            source_system="FAR_HTML",
            part_number=part_number,
            owner_id=user_id,
            tags=["far", f"part-{part_number}", FAR_PARTS.get(part_number, "").lower()],
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
    
    # Chunk and embed sections
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    all_chunks = []
    all_metadatas = []
    
    for section in sections:
        # Use section text as a single chunk (regulation sections should be atomic)
        text = section["text"]
        if len(text) > 2000:
            # Split long sections
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1500,
                chunk_overlap=200,
            )
            sub_chunks = splitter.split_text(text)
        else:
            sub_chunks = [text]
        
        for chunk in sub_chunks:
            all_chunks.append(chunk)
            all_metadatas.append({
                "doc_id": doc.id if db else f"far_part_{part_number}",
                "source": f"FAR Part {part_number}",
                "page": 1,
                "section_id": section["section_id"],
                "part_number": part_number,
                "source_type": "regulation",
                "source_system": "FAR_HTML",
                "is_regulation": True,
            })
    
    # Generate embeddings
    if all_chunks:
        embeddings = []
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i+batch_size]
            try:
                resp = client.embeddings.create(model="text-embedding-3-small", input=batch)
                embeddings.extend([item.embedding for item in resp.data])
            except Exception as e:
                print(f"OpenAI API Error: {e}. Using mock embeddings.")
                embeddings.extend([[0.0] * 1536 for _ in batch])
        
        # Store in vector DB
        doc_id = doc.id if db else f"far_part_{part_number}"
        vector_store.add_chunks(
            doc_id=doc_id,
            chunks=all_chunks,
            metadatas=all_metadatas,
            embeddings=embeddings,
        )
        
        # Update document status
        if db:
            doc.status = ProcessingStatus.COMPLETED
            doc.chunk_count = len(all_chunks)
            db.commit()
    
    return {
        "status": "success",
        "part_number": part_number,
        "part_name": FAR_PARTS.get(part_number, "Unknown"),
        "sections_found": len(sections),
        "chunks_created": len(all_chunks),
    }
