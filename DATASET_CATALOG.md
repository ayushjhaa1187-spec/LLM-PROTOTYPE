# DATASET_CATALOG.md — Single Source of Truth for FAR Compliance Copilot Data Assets

> **Status Legend**: 🟢 Ingested | 🟡 Partially Ingested | 🔴 Not Started | 🔵 Planned

---

## 1. Primary Regulatory Sources

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| FAR (Federal Acquisition Regulation) | acquisition.gov | XML/HTML | 🔴 | P0 - Critical | Core regulatory text, all 53 parts |
| DFARS (Defense FAR Supplement) | acquisition.gov | XML/HTML | 🔴 | P0 - Critical | DoD-specific supplements |
| 48 CFR (Code of Federal Regulations) | govinfo.gov | XML | 🔴 | P0 - Critical | Full CFR Title 48 |
| FAR Clause Matrix | acquisition.gov | HTML/PDF | 🔴 | P1 - High | Clause applicability matrix |

## 2. Case Law & Decisions

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| GAO Bid Protest Decisions | gao.gov | HTML/PDF | 🔴 | P1 - High | ~1000 decisions/year since 2000 |
| COFC Opinions | uscfc.uscourts.gov | PDF | 🔴 | P2 - Medium | Court of Federal Claims |
| Board of Contract Appeals | asbca.mil, cbca.gov | PDF | 🔴 | P2 - Medium | ASBCA + CBCA decisions |
| CourtListener Case Law | courtlistener.com | API/JSON | 🟡 | P2 - Medium | General case law search |

## 3. Procurement Data

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| FPDS (Federal Procurement Data) | fpds.gov | XML/CSV | 🔴 | P1 - High | $600B+ annual procurement data |
| USAspending | usaspending.gov | API/CSV | 🔴 | P1 - High | Federal spending transparency |
| SAM.gov Opportunities | sam.gov | API/JSON | 🔴 | P2 - Medium | Active solicitations |
| SAM.gov Entity Data | sam.gov | API/CSV | 🔴 | P2 - Medium | Vendor registration data |
| CPARS (Contractor Performance) | cpars.gov | Limited | 🔴 | P3 - Low | Past performance ratings |

## 4. Compliance & Security Standards

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| OSCAL/FedRAMP Controls | pages.nist.gov | JSON/XML | 🔴 | P1 - High | Machine-readable security controls |
| NIST 800-53 Controls | csrc.nist.gov | JSON/XML | 🔴 | P1 - High | Security and privacy controls |
| NIST 800-171 (CUI) | csrc.nist.gov | PDF | 🔴 | P1 - High | Controlled Unclassified Info protection |
| CMMC Assessment Guide | acq.osd.mil | PDF | 🔴 | P1 - High | Cybersecurity maturity model |
| Section 508 Standards | section508.gov | HTML | 🔴 | P2 - Medium | Accessibility requirements |

## 5. Inspector General & Audit Reports

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| GAO Reports | gao.gov | PDF/HTML | 🔴 | P2 - Medium | Government accountability reports |
| DoD OIG Reports | dodig.mil | PDF | 🔴 | P2 - Medium | Defense IG reports |
| Agency IG Reports | oversight.gov | PDF | 🔴 | P2 - Medium | Multi-agency IG reports |
| Improper Payments Data | paymentaccuracy.gov | CSV | 🔴 | P2 - Medium | Improper payments by agency |

## 6. Financial & Risk Datasets (Kaggle + HuggingFace)

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| SEC 10-K Filings | SEC EDGAR | XBRL/HTML | 🟡 | P2 - Medium | Vendor financial analysis |
| Banking Risk Indicators | Kaggle | CSV | 🔴 | P3 - Low | Financial stability indicators |
| Corporate Governance | Kaggle | CSV | 🔴 | P3 - Low | Board composition data |
| Bankruptcy Prediction | Kaggle | CSV | 🔴 | P3 - Low | Vendor risk modeling |
| Government Budget Data | USAspending | CSV | 🔴 | P2 - Medium | Congressional appropriations |

## 7. Specialized LLM Training Data

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| FineWeb-Edu (Legal subset) | HuggingFace | Parquet | 🔴 | P3 - Low | Pre-training data |
| Cosmopedia (Gov subset) | HuggingFace | Parquet | 🔴 | P3 - Low | Synthetic textbook data |
| Legal-BERT Corpus | HuggingFace | Text | 🔴 | P3 - Low | Legal domain pre-training |
| Government Contract QA | Custom | JSONL | 🔴 | P2 - Medium | Fine-tuning instruction pairs |

## 8. Congressional & Budget

| Dataset | Source | Format | Status | Priority | Notes |
|---------|--------|--------|--------|----------|-------|
| Congressional Budget Justifications | Various agencies | PDF | 🔴 | P3 - Low | Agency budget requests |
| FOIA Logs | Various agencies | CSV/PDF | 🔴 | P3 - Low | Freedom of Information requests |
| Federal Register Notices | federalregister.gov | API/JSON | 🔴 | P2 - Medium | Rulemaking and notices |

---

## Ingestion Pipeline Status

```
Raw Data → Validation → Processing → Embedding → Vector Store → Available
   ↓           ↓            ↓           ↓            ↓            ↓
  S3/Local   Schema      Chunking    OpenAI      ChromaDB    RAG Pipeline
             Check     + Metadata   Embedding    /pgvector
```

## Data Quality Requirements

| Check | Threshold | Description |
|-------|-----------|-------------|
| Row Count | > 0 | Must have at least some data |
| Null Ratio | < 20% | Key fields must not be majority null |
| Schema Match | 100% | Must match expected schema |
| Encoding | UTF-8 | All text must be valid UTF-8 |
| Deduplication | < 5% duplicates | Near-duplicate detection |

## Update Schedule

| Source | Frequency | Method |
|--------|-----------|--------|
| FAR/DFARS | Quarterly | Manual download + automated parsing |
| GAO Decisions | Monthly | Web scraping |
| FPDS Data | Weekly | API pull |
| NIST Controls | On update | Manual review + download |
| Kaggle/HF | As needed | API download |

---

*Last updated: 2026-03-04*
*Maintained by: FAR Compliance Copilot Team*
