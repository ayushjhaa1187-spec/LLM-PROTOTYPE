"""Regulation-aware smart chunking service.

Preserves FAR/DFARS section boundaries during document processing.
"""

import re
from typing import List, Dict, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings


class RegulationTextSplitter:
    """Smart text splitter for government regulations."""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        self.chunk_size = chunk_size or getattr(settings, "CHUNK_SIZE", 1000)
        self.chunk_overlap = chunk_overlap or getattr(settings, "CHUNK_OVERLAP", 200)
        
        # Regulation-specific separators
        self.separators = [
            r'\n(?=\d+\.\d+(?:-\d+)?\s*[A-Z])', # Section boundaries
            r'\n(?=\([a-z]\))',               # Subsection boundaries
            r'\n(?=\(\d+\))',                 # Numbered paragraphs
            '\n\n',
            '\n',
            '. ',
            ' '
        ]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            keep_separator=True,
            is_separator_regex=True
        )

    def split_regulation(self, text: str, metadata: Dict) -> List[Document]:
        """Split regulation text into section-aware documents."""
        # Find sections
        section_pattern = re.compile(r'^(\d+\.\d+(?:-\d+)?)\s+([A-Z][^.]+)', re.MULTILINE)
        matches = list(section_pattern.finditer(text))
        
        if not matches:
            # Fallback to standard split if no section patterns found
            chunks = self.splitter.split_text(text)
            return [Document(page_content=c, meta_data=metadata) for c in chunks]
            
        docs = []
        for i, match in enumerate(matches):
            section_id = match.group(1)
            section_title = match.group(2).strip()
            start = match.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            
            content = text[start:end].strip()
            
            # Sub-split if section is too large
            if len(content) > self.chunk_size:
                sub_chunks = self.splitter.split_text(content)
                for j, sub_chunk in enumerate(sub_chunks):
                    meta = metadata.copy()
                    meta.update({
                        'section_id': section_id,
                        'section_title': section_title,
                        'chunk_index': j,
                        'is_regulation': True
                    })
                    docs.append(Document(page_content=sub_chunk, metadata=meta))
            else:
                meta = metadata.copy()
                meta.update({
                    'section_id': section_id,
                    'section_title': section_title,
                    'is_regulation': True
                })
                docs.append(Document(page_content=content, metadata=meta))
                
        return docs


regulation_splitter = RegulationTextSplitter()
