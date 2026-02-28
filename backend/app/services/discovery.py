"""Discovery service for finding and cataloging high-value LLM training and RAG datasets."""

DATABASES = {
    "SEC_EDGAR": {
        "description": "US SEC 10-K Filings for financial compliance analysis.",
        "huggingface": "eloukas/edgar-corpus",
        "api": "https://www.sec.gov/edgar/sec-api-documentation",
        "category": "Finance/Compliance"
    },
    "THE_FREE_LAW": {
        "description": "CourtListener API and RECAP archive for case law.",
        "api": "https://www.courtlistener.com/api/v4/",
        "category": "Legal"
    },
    "COMMON_CORPUS": {
        "description": "2.2 Trillion tokens of open/compliant text (Legal, Gov, Sci).",
        "huggingface": "PleIAs/common-corpus",
        "category": "General Training"
    },
    "PUBMED": {
        "description": "Biomedical literature for healthcare compliance.",
        "huggingface": "ncbi/pubmed",
        "category": "Medical"
    },
    "FINEWEB": {
        "description": "High-quality educational web data.",
        "huggingface": "HuggingFaceFW/fineweb-edu",
        "category": "Pre-training"
    },
    "CASE_LAW_SUMM": {
        "description": "Gold standard case law summarization (Syllabuses).",
        "huggingface": "ChicagoHAI/CaseSumm",
        "category": "Legal/NLP"
    },
    "GRETEL_SYNTHETIC": {
        "description": "Synthetic legal and privacy-preserving data generation.",
        "api": "https://gretel.ai/",
        "category": "Synthetic/Privacy"
    },
    "COMMON_CRAWL": {
        "description": "Petabytes of web data (raw resource for LLM training).",
        "url": "https://commoncrawl.org/",
        "category": "Global Scale"
    }
}

def get_recommended_datasets():
    """Returns a list of recommended datasets for the current platform."""
    return [
        {"id": k, **v} for k, v in DATABASES.items()
    ]

def get_platform_links():
    """Returns links to primary training data platforms."""
    return {
        "HuggingFace": "https://huggingface.co/datasets",
        "Kaggle": "https://www.kaggle.com/datasets",
        "BrightData": "https://brightdata.com/products/datasets",
        "ScaleAI": "https://scale.com/open-av-dataset",
        "Appen": "https://appen.com/datasets/",
        "GitHub_Stack": "https://huggingface.co/datasets/bigcode/the-stack"
    }
