"""Robust citation verification service for FAR/DFARS compliance.

Prevents LLM hallucinations by verifying all citations against source documents
using regex patterns and metadata matching.
"""

import re
from typing import List, Dict, TypedDict, Optional, Any
from dataclasses import dataclass
from app.config import settings


@dataclass
class CitationMatch:
    """Represents a verified or hallucinated citation."""
    citation: str
    citation_type: str  # FAR, DFARS, CFR, GAO, etc.
    verified: bool
    source_document: Optional[str]
    section_id: Optional[str]
    page_number: Optional[int]
    confidence: float
    snippet: Optional[str]


class CitationVerificationResult(TypedDict):
    """Complete verification result for an LLM response."""
    verified_citations: List[CitationMatch]
    hallucinations: List[CitationMatch]
    overall_confidence: float
    confidence_label: str  # HIGH, MEDIUM, LOW
    requires_human_review: bool
    blocking_reason: Optional[str]


# Citation extraction patterns
CITATION_PATTERNS = {
    'FAR': [
        r'FAR\s+(\d+\.\d+(?:-\d+)?(?:\([a-z]|\(\d+\))*)',
        r'48\s+CFR\s+(\d+\.\d+(?:-\d+)?)',
        r'Federal\s+Acquisition\s+Regulation\s+(\d+\.\d+)'
    ],
    'DFARS': [
        r'DFARS\s+(\d+\.\d+(?:-\d+)?)',
        r'48\s+CFR\s+2(\d+\.\d+(?:-\d+)?)',
        r'Defense\s+Federal\s+Acquisition\s+Regulation\s+(\d+\.\d+)'
    ],
    'CFR': [
        r'(\d+)\s+CFR\s+(\d+\.\d+)',
        r'Code\s+of\s+Federal\s+Regulations\s+(\d+\.\d+)'
    ],
    'GAO': [
        r'GAO\s+([A-Z]-\d+-\d+)',
        r'GAO\s+Decision\s+([A-Z]-\d+-\d+)',
        r'B-\d+'
    ],
    'NIST': [
        r'NIST\s+SP\s+(\d+-\d+)',
        r'NIST\s+800-(\d+)',
        r'Special\s+Publication\s+(\d+-\d+)'
    ],
    'CMMC': [
        r'CMMC\s+(\d+\.\d+)',
        r'Cybersecurity\s+Maturity\s+Model\s+(\d+\.\d+)'
    ]
}


def extract_all_citations(text: str) -> List[Dict[str, str]]:
    """Extract all regulatory citations from text."""
    citations = []
    
    for citation_type, patterns in CITATION_PATTERNS.items():
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                citations.append({
                    'type': citation_type,
                    'citation': match.group(1),
                    'full_match': match.group(0)
                })
    
    # De-duplicate
    unique = []
    seen = set()
    for c in citations:
        key = f"{c['type']}:{c['citation']}"
        if key not in seen:
            seen.add(key)
            unique.append(c)
    
    return unique


def verify_citation_against_documents(
    citation: Dict[str, str],
    source_documents: List[Any]
) -> CitationMatch:
    """Verify a single citation against source documents."""
    citation_type = citation['type']
    citation_value = citation['citation']
    
    # Normalize
    normalized = re.sub(r'\s+', '', citation_value)
    
    for doc in source_documents:
        # Check metadata
        doc_meta = getattr(doc, 'metadata', {}) if not isinstance(doc, dict) else doc.get('metadata', {})
        doc_content = getattr(doc, 'page_content', '') if not isinstance(doc, dict) else doc.get('text', '')
        
        doc_section_id = doc_meta.get('section_id', '')
        
        # Exact match or prefix match in metadata
        if doc_section_id and (normalized.lower() in doc_section_id.lower() or doc_section_id.startswith(normalized)):
            return CitationMatch(
                citation=citation['full_match'],
                citation_type=citation_type,
                verified=True,
                source_document=doc_meta.get('source_system'),
                section_id=doc_section_id,
                page_number=doc_meta.get('page_number'),
                confidence=1.0,
                snippet=doc_content[:200]
            )
        
        # Check content
        if re.search(re.escape(normalized), doc_content, re.IGNORECASE):
            return CitationMatch(
                citation=citation['full_match'],
                citation_type=citation_type,
                verified=True,
                source_document=doc_meta.get('source_system'),
                section_id=doc_section_id,
                page_number=doc_meta.get('page_number'),
                confidence=0.9,
                snippet=doc_content[:200]
            )
    
    return CitationMatch(
        citation=citation['full_match'],
        citation_type=citation_type,
        verified=False,
        source_document=None,
        section_id=None,
        page_number=None,
        confidence=0.0,
        snippet=None
    )


def verify_citations_robust(
    response_text: str,
    source_documents: List[Any],
    threshold: float = None
) -> CitationVerificationResult:
    """Verify all citations in response against source documents."""
    if threshold is None:
        threshold = settings.CITATION_CONFIDENCE_THRESHOLD
    
    extracted_citations = extract_all_citations(response_text)
    
    if not extracted_citations:
        return {
            'verified_citations': [],
            'hallucinations': [],
            'overall_confidence': 0.0,
            'confidence_label': "LOW",
            'requires_human_review': True,
            'blocking_reason': "No citations found in response"
        }
    
    verified = []
    hallucinations = []
    
    for citation in extracted_citations:
        match = verify_citation_against_documents(citation, source_documents)
        if match.verified:
            verified.append(match)
        else:
            hallucinations.append(match)
    
    total = len(verified) + len(hallucinations)
    overall_confidence = sum(m.confidence for m in verified) / total if total > 0 else 0.0
    
    # Labeling
    if overall_confidence >= 0.8:
        confidence_label = "HIGH"
    elif overall_confidence >= 0.5:
        confidence_label = "MEDIUM"
    else:
        confidence_label = "LOW"
    
    # Decisions
    requires_human_review = (
        overall_confidence < threshold or 
        len(hallucinations) > 0 or 
        len(verified) == 0
    )
    
    blocking_reason = None
    if settings.BLOCK_LOW_CONFIDENCE and overall_confidence < threshold:
        blocking_reason = f"Citation confidence {overall_confidence:.2f} below threshold {threshold}"
    elif len(hallucinations) > 0:
        blocking_reason = f"Found {len(hallucinations)} unverified citations"
    
    return {
        'verified_citations': verified,
        'hallucinations': hallucinations,
        'overall_confidence': overall_confidence,
        'confidence_label': confidence_label,
        'requires_human_review': requires_human_review,
        'blocking_reason': blocking_reason
    }
