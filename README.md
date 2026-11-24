# REV: RAG for Engine & Vehicle Diagnostics

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![CUDA Accelerated](https://img.shields.io/badge/PyTorch-CUDA%20RTX%203050-green.svg)](https://pytorch.org/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20(Llama--3.2--3B)-purple.svg)](https://ollama.com/)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit%20Dashboard-red.svg)](https://streamlit.io/)
[![Unit Tests](https://img.shields.io/badge/Tests-41%2F41%20Passing-brightgreen.svg)](tests/)

> **REV** (**R**AG for **E**ngine & **V**ehicle Diagnostics) is a domain-specific, privacy-preserving, local Retrieval-Augmented Generation (RAG) system engineered for automotive mechanical troubleshooting, OBD-II diagnostic trouble code (DTC) analysis, and electronics repair.

It fuses dense semantic vector search (**ChromaDB** with **SentenceTransformers**) and sparse keyword retrieval (**Okapi BM25** from scratch), ranked via **Reciprocal Rank Fusion (RRF)**, **Maximum Marginal Relevance (MMR)**, and a **Cross-Feature Diagnostic Reranker**. Final responses are synthesized by a local **Ollama LLM (Llama 3.2)** and audited by real-time **grounding and hallucination guardrails**.

---

## Key System Features

- ⚡ **Dual-Mode Hybrid Search**: Combines semantic understanding of natural symptom complaints (*"engine shaking at idle"*) with exact alphanumeric matching of OBD-II codes (*"P0301"*).
- 🧠 **Local GPU LLM Synthesis (Ollama)**: Offline, privacy-preserving diagnostic generation powered by `llama3.2:3b` running on local CUDA VRAM.
- 🛡️ **Comprehensive Reliability & Security Guardrails**:
  - **Prompt Injection Defense**: Intercepts jailbreaks, DAN mode attacks, and malicious requests (e.g. vehicle hotwiring/tampering).
  - **Deterministic DTC Code Pruning**: Discards irrelevant nearest-neighbor candidate chunks when an unknown code (e.g. `P9999`) is requested.
  - **Pre-Generation Abstention Gate**: Suppresses LLM generation and returns a hardcoded `"No valid data found"` when evidence confidence is insufficient.
  - **Post-Generation Grounding Audit**: Validates bracketed citations (`[Source: fix_...]`) and audits numerical claims (labor hours, parts costs) against source metadata.
- 🔄 **Small-to-Big Context Expansion**: Indexes concise child chunks (~400 characters) for high retrieval precision, expanding to full parent technical repair guides during synthesis.
- 📊 **Automated Quantitative Benchmark Suite**: Computes Information Retrieval metrics (Hit Rate@K, MRR, Latency) and RAGAS metrics (Faithfulness, Relevancy, Abstention Accuracy).
- 🖥️ **Interactive Web UI (Streamlit)**: Complete dashboard featuring diagnostic guidance, retrieval ranking inspections, live model switching, temperature tuning, and OEM manual uploads.

---

## Architectural Flow

```
                      User Diagnostic Query
              (DTC Code + Observed Vehicle Symptoms)
                                 │
                                 ▼
                     [Pre-Retrieval Security]
                    detect_prompt_injection()
            (Intercepts Adversarial Jailbreaks & Tampering)
                                 │
                                 ▼
                    retrieval/multi_query.py
                (Acronym & Technical Code Expansion)
                                 │
          ┌──────────────────────┴──────────────────────┐
          ▼                                             ▼
 retrieval/vector_search.py                  retrieval/bm25_search.py
  (Dense Semantic Vector)                    (From-Scratch Okapi BM25)
  - ChromaDB HNSW Cosine                      - 1,787 technical terms
  - Captures fuzzy symptoms                   - 100% recall on codes (P0301)
          │                                             │
          └──────────────────────┬──────────────────────┘
                                 ▼
                        retrieval/rrf.py
                  (Reciprocal Rank Fusion - RRF)
                                 │
                                 ▼
                   retrieval/hybrid_search.py
                 (DTC Alignment & Candidate Pruning)
         (Eliminates irrelevant chunks if code is unknown)
                                 │
                                 ▼
                      retrieval/reranker.py
              (Cross-Feature Diagnostic Reranker)
              - DTC Code match bonus (+0.35)
              - Query token coverage (+0.25)
              - Authored diagnostic priority sequence
                                 │
                                 ▼
                   [Pre-Generation Safety Gate]
             verify_evidence_sufficiency() Threshold Check
          ┌──────────────────────┴──────────────────────┐
          ▼ (Evidence Insufficient / Unknown Code)      ▼ (Evidence Sufficient)
  [Hardcoded Abstention]                     generation/context_builder.py
"No valid data found..."                     (Small-to-Big Parent Expansion)
                                                        │
                                                        ▼
                                             Local LLM (Ollama)
                                          (Llama 3.2:3b Inference)
                                                        │
                                                        ▼
                                           [Post-Generation Safety Audit]
                                              generation/grounding.py
                                       (Citation Audit & Factual Verification)
                                                        │
                                                        ▼
                                            Verified Diagnostic Response
```

---

## Project Directory Layout

```text
AutoDiagnose/
│
├── data/
│   ├── raw/                  # MechanicDB CSVs, JSONs, and PDF manuals
│   │   ├── dtc_codes.csv
│   │   ├── diagnostic_fixes.csv
│   │   ├── replacement_parts.csv
│   │   ├── cost_metadata.json
│   │   └── ordering_metadata.json
│   ├── processed/            # Synthesized JSONL documents & BM25 index
│   │   ├── synthesized_documents.jsonl (416 full diagnostic guides)
│   │   ├── chunks.jsonl                (2,369 section-aware chunks)
│   │   └── bm25_index.pkl              (Serialized state-dict inverted index)
│   └── evaluation/           # Benchmark dataset & markdown reports
│       ├── benchmark_qa.json
│       └── benchmark_report.md
│
├── ingestion/
│   ├── inspect_dataset.py    # Exploratory Data Analysis & integrity checks
│   ├── document_loader.py    # CSV/JSON and PyMuPDF (fitz) PDF manual loader
│   ├── metadata.py           # Typed metadata schemas (DocumentMetadata)
│   ├── preprocessing.py      # Cleaning, step formatting, and document synthesis
│   ├── chunking.py           # Section-aware & recursive chunking from scratch
│   └── embedding.py          # Sentence Transformer local GPU embedding pipeline
│
├── vectorstore/
│   └── chroma_store.py       # Persistent ChromaDB collection manager (autodiagnose_kb)
│
├── retrieval/
│   ├── vector_search.py      # Dense semantic vector retriever
│   ├── bm25_search.py        # From-scratch Okapi BM25 lexical engine
│   ├── rrf.py                # Reciprocal Rank Fusion implementation
│   ├── mmr.py                # Maximum Marginal Relevance diversity filtering
│   ├── multi_query.py        # Technical acronym & code query expansion
│   ├── parent_child.py       # Small-to-big context expansion resolver
│   ├── reranker.py           # Cross-feature diagnostic reranker
│   └── hybrid_search.py      # Master hybrid retriever with DTC code alignment
│
├── generation/
│   ├── prompt.py             # Grounded system prompts & symptom reasoning templates
│   ├── context_builder.py    # Evidence formatting & token budgeting
│   ├── answer_generator.py   # Ollama API client, dynamic models, & offline fallback
│   └── grounding.py          # Prompt injection detection, sufficiency check & citation audit
│
├── evaluation/
│   ├── retrieval_metrics.py  # Hit Rate@K, Precision@K, Recall@K, and MRR
│   ├── ragas_evaluation.py   # Faithfulness, answer relevancy, and abstention accuracy
│   └── benchmark.py          # Comparative baseline vs. hybrid experiment runner
│
├── app/
│   └── ui.py                 # Streamlit web dashboard with live Ollama controls
│
├── tests/                    # 41 Passing automated unit & integration tests
│   ├── test_ingestion.py
│   ├── test_chunking.py
│   ├── test_vectorstore.py
│   ├── test_retrieval.py
│   ├── test_grounding.py
│   └── test_evaluation.py
│
├── config.py                 # Centralized configuration, hyperparameters, & paths
└── pyproject.toml            # Project dependencies and packaging
```

---

## Quantitative Benchmark Results

Evaluated across the standardized automotive benchmark test suite (Exact DTCs, multi-symptom descriptions, OEM-specific readiness codes, and adversarial negative queries):

| Metric | Baseline Dense RAG | Optimized Hybrid RAG | Delta (Gain) |
| :--- | :---: | :---: | :---: |
| **Hit Rate@1 (Top-1 Accuracy)** | 75.0% | **87.5%** | **+12.5%** |
| **Hit Rate@3** | 87.5% | **87.5%** | 0.0% |
| **Hit Rate@5** | 100.0% | **100.0%** | **100% Coverage** |
| **Mean Reciprocal Rank (MRR)** | 0.8229 | **0.9062** | **+0.0833** |
| **Mean Retrieval Latency** | 355.3 ms | **34.9 ms** | **-320.4 ms (10x faster)** |
| **Abstention Accuracy** | 100.0% | **100.0%** | **PASS (Zero Hallucination)** |

---

## Getting Started

### 1. Prerequisites
- Python 3.10+
- NVIDIA GPU with CUDA support
- [Ollama](https://ollama.com/) installed locally

### 2. Environment Setup
```powershell
# Clone or navigate to the project directory
cd e:\Vishwa\learning\RAG

# Install dependencies
pip install torch sentence-transformers chromadb streamlit pymupdf numpy
```

### 3. Start Local Ollama LLM
In a terminal, pull and start Meta's Llama 3.2 (3B):
```powershell
ollama run llama3.2:3b
```
*(The model will be cached locally on your machine and run with GPU acceleration).*

---

## Execution Pipeline

### Step 1: Data Preparation & Ingestion
```powershell
# Run exploratory data analysis on MechanicDB
python ingestion/inspect_dataset.py

# Synthesize structured diagnostic documents
python ingestion/preprocessing.py

# Generate section-aware chunks
python ingestion/chunking.py

# Test embedding generation on CUDA GPU
python ingestion/embedding.py
```

### Step 2: Indexing & Hybrid Search
```powershell
# Populate ChromaDB collection with 2,369 chunks
python vectorstore/chroma_store.py

# Build and serialize the Okapi BM25 inverted index
python retrieval/bm25_search.py

# Run hybrid retrieval verification
python retrieval/hybrid_search.py
```

### Step 3: Test Grounded Generation
```powershell
# Test end-to-end evidence generation and guardrails
python generation/answer_generator.py
```

### Step 4: Run Evaluation Benchmarks
```powershell
# Run baseline vs. hybrid comparative benchmark
python evaluation/benchmark.py
```

### Step 5: Launch Web Application Dashboard
```powershell
python -m streamlit run app/ui.py
```
Open **`http://localhost:8501`** in your browser.

---

## Running Automated Tests

Run the full automated test suite (41 tests):
```powershell
python -m unittest discover tests
```

Expected output:
```text
Ran 41 tests in 6.431s

OK
```

---

## License

This project is developed for educational, diagnostic research, and automotive engineering purposes. All diagnostic trouble codes and procedures conform to standard SAE J1979 / ISO 15031 OBD-II specifications.
