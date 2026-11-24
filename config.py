"""
AutoDiagnose: Centralized Configuration File
Contains paths, model parameters, chunking settings, and retrieval hyperparameters.
"""
from pathlib import Path

# --- Path Configurations ---
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EVALUATION_DATA_DIR = DATA_DIR / "evaluation"

VECTORSTORE_DIR = BASE_DIR / "vectorstore" / "chroma_db"

# Raw Data File Paths
DTC_CODES_CSV = RAW_DATA_DIR / "dtc_codes.csv"
DIAGNOSTIC_FIXES_CSV = RAW_DATA_DIR / "diagnostic_fixes.csv"
DTC_FIXES_JOINED_CSV = RAW_DATA_DIR / "dtc_fixes_joined.csv"
REPLACEMENT_PARTS_CSV = RAW_DATA_DIR / "replacement_parts.csv"
COST_METADATA_JSON = RAW_DATA_DIR / "cost_metadata.json"
ORDERING_METADATA_JSON = RAW_DATA_DIR / "ordering_metadata.json"
IDENTITY_MAP_CSV = RAW_DATA_DIR / "identity_map.csv"

# Processed Data Paths
SYNTHESIZED_DOCS_JSONL = PROCESSED_DATA_DIR / "synthesized_documents.jsonl"
CHUNKS_JSONL = PROCESSED_DATA_DIR / "chunks.jsonl"

# --- Embedding Configurations ---
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # Fast, lightweight, 384 dims
EMBEDDING_DIMENSION = 384

# --- ChromaDB Configurations ---
CHROMA_COLLECTION_NAME = "autodiagnose_kb"

# --- Chunking Configurations ---
CHUNK_SIZE = 400       # Target token/character window for child chunks
CHUNK_OVERLAP = 50     # Overlap for continuity

# --- Retrieval Configurations ---
DEFAULT_TOP_K = 5
HYBRID_VECTOR_WEIGHT = 0.5
HYBRID_BM25_WEIGHT = 0.5
RRF_K_CONSTANT = 60
MMR_LAMBDA = 0.7

# --- Generation Configurations (Local Ollama) ---
OLLAMA_HOST = "http://localhost:11434"
DEFAULT_LLM_MODEL = "llama3.2:3b"
TEMPERATURE = 0.1  # Strict factual grounding, low randomness
MAX_TOKENS = 768
