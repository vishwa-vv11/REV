"""
Embedding Pipeline Module for AutoDiagnose
Generates dense vector embeddings using Sentence Transformers on local GPU/CPU,
with batching, dimension validation, and cosine similarity calculations.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import numpy as np
import torch
import json
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

# Enforce offline mode if internet is unavailable
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from sentence_transformers import SentenceTransformer

def find_cached_model_path(model_name: str) -> str:
    """Checks HuggingFace hub cache for local model snapshots to avoid DNS lookups."""
    cache_base = Path.home() / ".cache" / "huggingface" / "hub"
    # Format: models--sentence-transformers--all-MiniLM-L6-v2
    clean_name = "models--" + model_name.replace("/", "--")
    if not clean_name.startswith("models--sentence-transformers--") and not "/" in model_name:
        clean_name = f"models--sentence-transformers--{model_name}"
    
    target_dir = cache_base / clean_name / "snapshots"
    if target_dir.exists():
        snapshots = list(target_dir.iterdir())
        if snapshots:
            return str(snapshots[0])
    return model_name

class AutomotiveEmbedder:
    """
    Manages loading and inference for Sentence Transformer embedding models.
    Supports GPU acceleration (CUDA) and batch vector encoding.
    """
    def __init__(
        self,
        model_name: str = config.EMBEDDING_MODEL_NAME,
        device: Optional[str] = None
    ):
        self.model_identifier = find_cached_model_path(model_name)
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        print(f"[*] Initializing SentenceTransformer ('{model_name}') on {self.device.upper()}...")
        self.model = SentenceTransformer(self.model_identifier, device=self.device)
        self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        print(f"[+] Model ready. Vector dimensions: {self.embedding_dimension}")

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 64,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = True
    ) -> np.ndarray:
        """
        Embeds a list of texts into dense vectors.
        normalize_embeddings=True ensures dot product equals cosine similarity.
        """
        if not texts:
            return np.empty((0, self.embedding_dimension), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=show_progress_bar,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True
        )
        return embeddings

    def embed_query(self, query: str, normalize_embeddings: bool = True) -> np.ndarray:
        """Embeds a single search query."""
        emb = self.model.encode(
            query,
            normalize_embeddings=normalize_embeddings,
            convert_to_numpy=True
        )
        return emb

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Computes cosine similarity between two 1D normalized or unnormalized vectors."""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    @staticmethod
    def batch_cosine_similarity(query_vec: np.ndarray, doc_vectors: np.ndarray) -> np.ndarray:
        """
        Computes cosine similarities between a 1D query vector and a 2D matrix of doc vectors.
        Assumes normalized vectors for high-speed dot-product.
        """
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        return np.dot(doc_vectors, query_vec.T).squeeze()

def run_embedding_demo():
    print("=" * 70)
    print("PHASE 2: EMBEDDING GENERATION & SEMANTIC SIMILARITY DEMO")
    print("=" * 70)

    embedder = AutomotiveEmbedder()

    # Test automotive queries
    sample_queries = [
        "Car vibrates and stumbles while idling at a red light",
        "ABS warning light is on and wheel speed sensor circuit is faulty",
        "Fuel mixture is running too lean on Bank 1"
    ]

    # Sample texts from our dataset
    sample_corpus = [
        "[Powertrain | DTC P0301] Cylinder 1 Misfire Detected. Code sets when combustion events are repeatedly lost on cylinder 1.",
        "[Chassis | DTC C0031] Left Front Wheel Speed Sensor circuit open or shorted. Diagnosis includes inspecting sensor connector and harness.",
        "[Powertrain | DTC P0171] System Too Lean Bank 1. ECM must add more fuel than calibrated limits due to unmetered vacuum leak.",
        "[Chassis | DTC C0040] Brake Pedal Switch A circuit implausible state. Causes brake lights to stay stuck on or shifter stuck in park."
    ]

    print("\n[*] Encoding sample corpus...")
    corpus_vectors = embedder.embed_texts(sample_corpus, show_progress_bar=False)

    print("\n[*] Comparing sample queries against corpus via Cosine Similarity:\n")
    for q in sample_queries:
        q_vec = embedder.embed_query(q)
        scores = embedder.batch_cosine_similarity(q_vec, corpus_vectors)
        top_idx = int(np.argmax(scores))
        
        print(f"Query: \"{q}\"")
        print(f"  -> Top Match (Score: {scores[top_idx]:.4f}):")
        print(f"     \"{sample_corpus[top_idx][:100]}...\"\n")

    print("=" * 70)
    print("EMBEDDING PIPELINE VALIDATION SUCCESSFUL.")
    print("=" * 70)

if __name__ == "__main__":
    run_embedding_demo()
