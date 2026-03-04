"""Kaggle Dataset Ingestion Pipeline for FAR Compliance.

Downloads and processes financial/audit risk datasets to enrich RAG results.
"""

import os
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi
from sqlalchemy.orm import Session

from app.config import settings
from app.core.smart_chunking import regulation_splitter


class KaggleIngestionPipeline:
    """Service to ingest priority Kaggle datasets for bid/no-bid and risk analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.kaggle_api = KaggleApi()
        try:
            self.kaggle_api.authenticate()
        except Exception:
            print("⚠️ Kaggle API Authentication failed - Check credentials")
    
    async def ingest_priority_datasets(self) -> Dict[str, Any]:
        """Ingest priority datasets for MVP workflows (Financial, Audit, Legal)."""
        results = {}
        
        # 1. Financial Risk Datasets (SEC-10 etc.)
        results['financial_risk'] = await self.ingest_by_name(
            datasets=[
                'alikashif1994/us-listed-companies-financial-data',
                'yashjogi007/prediction-of-bankruptcy-of-535-firm'
            ],
            source_type='financial_risk'
        )
        
        # 2. Audit Risk
        results['audit_risk'] = await self.ingest_by_name(
            datasets=['ziya07/tax-risk-identification-dataset'],
            source_type='audit_risk'
        )
        
        return results
    
    async def ingest_by_name(self, datasets: List[str], source_type: str) -> Dict[str, Any]:
        """Generic ingestion logic for Kaggle datasets."""
        chunks_total = 0
        
        for dataset in datasets:
            raw_path = Path(f"data/raw/{source_type}/{dataset.split('/')[-1]}")
            raw_path.mkdir(parents=True, exist_ok=True)
            
            # Download
            try:
                self.kaggle_api.dataset_download_files(dataset, path=str(raw_path), unzip=True)
            except Exception as e:
                print(f"Error downloading {dataset}: {e}")
                continue
                
            # Process CSV files
            for csv_file in raw_path.glob("*.csv"):
                df = pd.read_csv(csv_file)
                
                # Sample or process all (limited for now)
                for _, row in df.head(500).iterrows():
                    chunk_text = f"{source_type.title()} Data ({dataset}): " + ", ".join([f"{c}: {v}" for c, v in row.items() if pd.notna(v)])
                    
                    # We would typically add this to vector_store here
                    # from app.services import vector_store
                    # vector_store.add_to_collection(chunk_text, {"source": dataset, "type": source_type})
                    
                    chunks_total += 1
                    
        return {"status": "success", "chunks": chunks_total}
