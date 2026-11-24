"""
Maximum Marginal Relevance (MMR) Module for AutoDiagnose
Filters redundant search results to maximize diagnostic diversity across procedures.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.embedding import AutomotiveEmbedder

def compute_mmr(
    query_vector: np.ndarray,
    candidate_vectors: np.ndarray,
    candidates: List[Dict[str, Any]],
    top_k: int = config.DEFAULT_TOP_K,
    lambda_param: float = config.MMR_LAMBDA
) -> List[Dict[str, Any]]:
    """
    Selects top_k diverse candidates using Maximum Marginal Relevance (MMR).
    
    Formula:
        MMR = argmax_{d in R \ S} [ lambda * Sim(d, Q) - (1 - lambda) * max_{s in S} Sim(d, s) ]
    """
    if len(candidates) == 0:
        return []

    if len(candidates) <= top_k:
        return candidates

    # Normalize vectors for cosine similarity via dot product
    norm_q = query_vector / np.linalg.norm(query_vector) if np.linalg.norm(query_vector) > 0 else query_vector
    norm_c = candidate_vectors / np.linalg.norm(candidate_vectors, axis=1, keepdims=True)

    # Similarity to query: (N,)
    query_sims = np.dot(norm_c, norm_q)

    # Similarity matrix among candidates: (N, N)
    doc_sim_matrix = np.dot(norm_c, norm_c.T)

    selected_indices: List[int] = []
    unselected_indices: List[int] = list(range(len(candidates)))

    # First document is the one with highest similarity to query
    first_idx = int(np.argmax(query_sims))
    selected_indices.append(first_idx)
    unselected_indices.remove(first_idx)

    # Greedily select remaining documents
    while len(selected_indices) < top_k and unselected_indices:
        mmr_scores = []
        for idx in unselected_indices:
            sim_to_query = query_sims[idx]
            max_sim_to_selected = max(doc_sim_matrix[idx, s_idx] for s_idx in selected_indices)
            mmr_val = lambda_param * sim_to_query - (1.0 - lambda_param) * max_sim_to_selected
            mmr_scores.append((mmr_val, idx))

        # Pick candidate with highest MMR score
        mmr_scores.sort(key=lambda x: x[0], reverse=True)
        best_val, best_idx = mmr_scores[0]
        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)

    # Format diverse results
    diverse_results = []
    for rank, idx in enumerate(selected_indices, 1):
        item = dict(candidates[idx])
        item["mmr_rank"] = rank
        diverse_results.append(item)

    return diverse_results
