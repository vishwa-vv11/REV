# AutoDiagnose: Automotive Diagnostic Intelligence using Retrieval-Augmented Generation (RAG)

**Domain:** Car Diagnostic Service and Electronics Repair  
**Core Technologies:** Python, Local LLM (Ollama), ChromaDB, Sentence Transformers, BM25, RAGAS, Streamlit

---

## 1. Problem Statement & Proposed Solution

### The Problem
When a vehicle experiences a mechanical or electronic issue, drivers and mechanics often face fragmented diagnostic information:
* The check-engine light (MIL) illuminates.
* The engine exhibits rough idling, vibrations, or unusual noises.
* An OBD-II scanner outputs a Diagnostic Trouble Code (DTC), such as `P0301`.

Currently, troubleshooting requires manually cross-referencing scattered sources:
1. OBD-II diagnostic code databases
2. Vehicle service manuals
3. Repair guides and technical service bulletins (TSBs)
4. Replacement parts documentation
5. General troubleshooting logs

**Core Challenge:** How can we build an intelligent system that retrieves relevant automotive technical knowledge and generates accurate, evidence-backed troubleshooting guidance?

### The Proposed Solution: AutoDiagnose
**AutoDiagnose** is a locally hosted, RAG-powered automotive troubleshooting assistant. Users input a DTC code, vehicle details, observed symptoms, or any combination thereof. The system retrieves relevant technical records from a curated vector and keyword knowledge base and synthesizes a grounded response using a local Large Language Model (LLM).

#### Example Interaction
* **User Query:** *"My car displays P0301, and the engine vibrates while idling. What could be the problem?"*
* **Expected System Response:**
  * **Diagnostic Code:** `P0301` — Cylinder 1 misfire detected.
  * **Possible Causes:** Ignition coil failure, fouled or worn spark plug, faulty fuel injector, or low cylinder compression.
  * **Recommended Inspections:** Inspect the Cylinder 1 spark plug, test or swap the ignition coil, and verify fuel injector operation.
  * **Evidence:** Citations to the retrieved diagnostic records and repair guides.
  * **Confidence & Limitations:** The code confirms a misfire in Cylinder 1, but physical inspection is required to isolate the exact faulty component.

> **Critical Design Constraint:** AutoDiagnose must clearly distinguish between *possible causes* and a *confirmed diagnosis*. It must strictly abstain from inventing repair procedures when the retrieved knowledge base lacks supporting evidence.

---

## 2. Project Objectives

1. **Knowledge Base Construction:** Transform structured automotive datasets and unstructured manuals into a rich, metadata-preserved knowledge base.
2. **Dual-Mode Retrieval:** Combine dense semantic vector search with sparse keyword matching (BM25).
3. **Retrieval Optimization:** Implement advanced RAG techniques (RRF, MMR, Multi-Query, Parent-Child retrieval, and Cross-Encoder reranking).
4. **Grounded Generation:** Generate clear, actionable troubleshooting steps using a local LLM via Ollama.
5. **Hallucination Mitigation:** Enforce strict prompt grounding, evidence sufficiency checks, and graceful abstention.
6. **Quantitative Evaluation:** Benchmark retrieval and generation quality using standard IR metrics and the RAGAS framework.
7. **Interactive Application:** Deliver a clean, inspectable user interface built with Streamlit.

---

## 3. System Architecture

```text
+-------------------------------------------------------------------+
|                            USER QUERY                             |
|              (DTC Code + Symptoms + Vehicle Details)              |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        1. QUERY PROCESSING                        |
|   Query Cleaning  |  Multi-Query Generation  |  Intent Parsing    |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                        2. RETRIEVAL ENGINE                        |
|  +-----------------------------+  +----------------------------+  |
|  |        Vector Search        |  |        BM25 Search         |  |
|  |    (Semantic Similarity)    |  |     (Keyword Matching)     |  |
|  +--------------+--------------+  +-------------+--------------+  |
|                 |                               |                 |
|                 +---------------+---------------+                 |
|                                 |                                 |
|                                 v                                 |
|   Hybrid Search -> RRF -> Metadata Filtering -> MMR -> Reranking  |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                      3. CONTEXT CONSTRUCTION                      |
|      Parent-Child Expansion  |  Metadata Formatting  |  Dedupe    |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                         4. LLM GENERATION                         |
|      Local LLM (Ollama)  |  Strict Grounding System Prompt        |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                     5. VALIDATION & ABSTENTION                    |
|     Hallucination Check  |  Evidence Sufficiency Verification     |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|                          FINAL RESPONSE                           |
|       Troubleshooting Guidance + Supporting Source Citations      |
+-------------------------------------------------------------------+
```

---

## 4. Dataset & Knowledge Base Strategy

The initial knowledge base is built from the **MechanicDB** dataset, structured across five core files:

| File Name | Role in AutoDiagnose |
| :--- | :--- |
| `dtc_codes.csv` | Standard OBD-II code definitions and descriptions. |
| `diagnostic_fixes.csv` | Known troubleshooting steps, root causes, and repair procedures. |
| `dtc_fixes_joined.csv` | Relational mapping linking specific DTCs to verified fixes. |
| `replacement_parts.csv` | Component specifications and replacement part details. |
| `cost_metadata.json` | Estimated labor and part cost metadata for repair planning. |

### Data Transformation Philosophy
A raw CSV table is not inherently suitable for semantic retrieval. During ingestion, structured rows will be synthesized into coherent natural-language diagnostic documents while retaining all tabular attributes (e.g., `dtc_code`, `system_category`, `part_name`, `estimated_cost`) as structured metadata for filtering. In later iterations, this foundation will be extended with PDF vehicle service manuals via `PyMuPDF`.

---

## 5. Eight-Phase Implementation Roadmap

### Phase 1 — Data Ingestion and Preprocessing
* **Goal:** Inspect, clean, normalize, and transform raw CSV/JSON records into structured document objects.
* **Key Concepts:** Pandas EDA, missing value/duplicate handling, text normalization, document templating, metadata extraction.
* **Deliverable:** Clean, serialized automotive knowledge documents with preserved source IDs.

### Phase 2 — Chunking and Embeddings
* **Goal:** Segment documents optimally and convert them into dense vector representations.
* **Key Concepts:** Fixed-size, recursive, and semantic chunking; chunk overlap; metadata enrichment; vector dimensions; cosine similarity.
* **Deliverable:** Embedded automotive document chunks generated via `Sentence Transformers`.

### Phase 3 — Vector Database and Basic RAG
* **Goal:** Establish end-to-end vector storage, retrieval, and baseline LLM generation.
* **Key Concepts:** ChromaDB collections, Top-$K$ retrieval, similarity score thresholds, metadata filtering, context injection.
* **Deliverable:** First functional baseline AutoDiagnose RAG pipeline.

### Phase 4 — Advanced Retrieval Optimization
* **Goal:** Maximize retrieval precision and recall for complex, multi-symptom queries.
* **Key Concepts:** BM25 lexical search, Hybrid Search, Reciprocal Rank Fusion (RRF), Maximum Marginal Relevance (MMR), Multi-Query expansion, Parent-Child retrieval, Cross-Encoder reranking.
* **Deliverable:** High-precision hybrid retrieval engine.

### Phase 5 — Generation and Reliability
* **Goal:** Ensure generated answers are strictly faithful to retrieved evidence.
* **Key Concepts:** Prompt engineering, grounding constraints, hallucination suppression, insufficient-context detection, abstention logic, inline source citations.
* **Deliverable:** Evidence-grounded local LLM assistant powered by Ollama.

### Phase 6 — RAG Evaluation
* **Goal:** Quantitatively measure retrieval effectiveness and answer quality.
* **Key Concepts:** Synthetic/curated benchmark datasets, $\text{Precision@K}$, $\text{Recall@K}$, Mean Reciprocal Rank ($\text{MRR}$), RAGAS metrics (Faithfulness, Answer Relevancy, Context Precision, Context Recall).
* **Deliverable:** Comprehensive evaluation report comparing Baseline RAG vs. Optimized RAG.

### Phase 7 — Application Development
* **Goal:** Build an intuitive, transparent interface for end users and mechanics.
* **Key Concepts:** Streamlit UI, session state management, input validation, PDF manual upload support, retrieval debugging inspector.
* **Deliverable:** Interactive AutoDiagnose web dashboard.

### Phase 8 — Testing and Documentation
* **Goal:** Ensure system reliability, reproducibility, and production readiness.
* **Key Concepts:** Unit and integration testing (`pytest`), edge-case validation (unknown DTCs, conflicting vehicle metadata), latency profiling, architectural documentation.
* **Deliverable:** Complete, tested, GitHub-ready repository.

---

## 6. Technology Stack

To ensure deep understanding of underlying RAG mechanics, components are built directly in Python rather than abstracted behind high-level orchestration frameworks.

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core system implementation |
| **Data Processing** | Pandas | Tabular cleaning, joining, and transformation |
| **PDF Parsing** | PyMuPDF (`fitz`) | Extracting text from vehicle service manuals |
| **Embeddings** | Sentence Transformers | Local dense text embedding generation |
| **Vector Database** | ChromaDB | Persistent vector storage and metadata filtering |
| **Keyword Search** | `rank-bm25` | Sparse lexical retrieval for exact DTC/part matches |
| **Reranking** | Cross-Encoder | Fine-grained pairwise relevance scoring |
| **Local LLM** | Ollama | Privacy-preserving local inference and synthesis |
| **Evaluation** | RAGAS & Custom Metrics | Automated retrieval and generation benchmarking |
| **Frontend** | Streamlit | Interactive diagnostic UI and retrieval inspector |
| **Testing** | `pytest` | Automated unit and pipeline integration tests |

---

## 7. Project Folder Structure

```text
AutoDiagnose/
│
├── data/
│   ├── raw/                  # Original MechanicDB CSVs, JSONs, and PDF manuals
│   ├── processed/            # Cleaned and formatted JSONL document stores
│   └── evaluation/           # Benchmark Q&A pairs and ground-truth IDs
│
├── ingestion/
│   ├── inspect_dataset.py    # Exploratory data analysis scripts
│   ├── document_loader.py    # CSV/JSON/PDF ingestion handlers
│   ├── preprocessing.py      # Cleaning, normalization, and text synthesis
│   ├── chunking.py           # Fixed, recursive, and semantic chunking logic
│   ├── metadata.py           # Metadata schema enforcement
│   └── embedding.py          # Sentence Transformer embedding pipeline
│
├── vectorstore/
│   └── chroma_store.py       # ChromaDB collection management and persistence
│
├── retrieval/
│   ├── vector_search.py      # Dense semantic retrieval
│   ├── bm25_search.py        # Sparse keyword retrieval
│   ├── hybrid_search.py      # Combined dense + sparse orchestration
│   ├── rrf.py                # Reciprocal Rank Fusion implementation
│   ├── mmr.py                # Maximum Marginal Relevance diversity filtering
│   ├── multi_query.py        # LLM-based query expansion
│   ├── parent_child.py       # Small-to-big context retrieval
│   └── reranker.py           # Cross-encoder scoring and reordering
│
├── generation/
│   ├── prompt.py             # Grounded system prompts and templates
│   ├── context_builder.py    # Evidence formatting and token budgeting
│   ├── answer_generator.py   # Ollama API integration
│   └── grounding.py          # Citation verification and abstention checks
│
├── evaluation/
│   ├── retrieval_metrics.py  # Precision@K, Recall@K, MRR calculations
│   ├── ragas_evaluation.py   # Faithfulness and relevancy scoring
│   └── benchmark.py          # End-to-end experiment runner
│
├── app/
│   └── ui.py                 # Streamlit diagnostic dashboard
│
├── tests/                    # Automated pytest test suites
├── config.py                 # Centralized model, path, and hyperparameter settings
├── pyproject.toml            # Project dependencies and build metadata
└── README.md                 # Setup instructions and usage guide
```

---

## 8. Learning Methodology

Every technical module in AutoDiagnose follows a seven-step mastery cycle rather than blind code assembly:

1. **Conceptual Foundation:** Understand what the algorithm/technique is and what failure mode it solves.
2. **Automotive Contextualization:** Map the concept to a concrete diagnostic scenario (e.g., why BM25 is crucial for exact codes like `P0301` while vectors capture *"rough idle"*).
3. **From-Scratch Implementation:** Write clean, transparent Python code for the core logic (e.g., implementing RRF and MMR math manually).
4. **Output Inspection:** Print and examine intermediate artifacts—chunks, similarity matrices, rank shifts, and token counts.
5. **Parameter Experimentation:** Tune hyperparameters (chunk sizes, overlap, $\lambda$ in MMR, Top-$K$) and observe behavioral changes.
6. **Pipeline Integration:** Refactor the validated module into the main `AutoDiagnose` package.
7. **Knowledge Verification:** Review design trade-offs through targeted, interview-style technical questions.

---

## 9. Target Capabilities & Safety Boundary

### Final System Capabilities
* Look up standard and manufacturer-specific OBD-II Diagnostic Trouble Codes.
* Interpret natural-language symptom descriptions alongside structured vehicle metadata.
* Execute hybrid semantic + lexical retrieval with Cross-Encoder reranking.
* Deliver structured troubleshooting guidance backed by explicit source citations.
* Detect low-confidence or out-of-scope queries and safely abstain from answering.
* Provide transparent retrieval diagnostics and quantitative evaluation metrics.

### Safety & Operational Boundary
> **Disclaimer:** AutoDiagnose is an informational troubleshooting assistant, **not** a substitute for a certified automotive technician. It identifies probable causes based on retrieved technical records rather than issuing a confirmed mechanical diagnosis. All safety-critical procedures and vehicle-specific repair specifications must be verified against the official OEM service manual before performing physical repairs.