"""
Reciprocal Rank Fusion (RRF) Module for AutoDiagnose
Combines multiple ranked retrieval lists (Dense Vector + BM25 Lexical)
without requiring score calibration or normalization.
"""
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    weights: Optional[List[float]] = None,
    k_constant: int = config.RRF_K_CONSTANT,
    top_k: int = config.DEFAULT_TOP_K
) -> List[Dict[str, Any]]:
    """
    Fuses multiple ranked retrieval lists into a single consensus ranking using RRF.
    
    Formula:
        RRF_Score(d) = sum_{m in M} ( w_m / (k + rank_m(d)) )
    """
    if not ranked_lists:
        return []

    if weights is None:
        weights = [1.0] * len(ranked_lists)

    rrf_scores: Dict[str, float] = {}
    doc_payloads: Dict[str, Dict[str, Any]] = {}
    doc_sources: Dict[str, List[str]] = {}

    for list_idx, rank_list in enumerate(ranked_lists):
        w = weights[list_idx]
        for rank, item in enumerate(rank_list, 1):
            chunk_id = item["chunk_id"]

            if chunk_id not in doc_payloads:
                doc_payloads[chunk_id] = {
                    "chunk_id": chunk_id,
                    "text": item["text"],
                    "metadata": item["metadata"],
                    "vector_score": item.get("score") if list_idx == 0 else None
                }
                doc_sources[chunk_id] = []
            elif list_idx == 0 and item.get("score") is not None:
                doc_payloads[chunk_id]["vector_score"] = item.get("score")

            # Add reciprocal rank score
            reciprocal_score = w / (k_constant + rank)
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + reciprocal_score
            doc_sources[chunk_id].append(f"list_{list_idx}(rank_{rank})")

    # Sort documents by descending RRF score
    sorted_doc_ids = sorted(rrf_scores.keys(), key=lambda doc_id: rrf_scores[doc_id], reverse=True)[:top_k]

    fused_results = []
    for rank, doc_id in enumerate(sorted_doc_ids, 1):
        item = doc_payloads[doc_id]
        fused_results.append({
            "rank": rank,
            "chunk_id": doc_id,
            "rrf_score": float(rrf_scores[doc_id]),
            "vector_score": item.get("vector_score"),
            "text": item["text"],
            "metadata": item["metadata"],
            "contributing_sources": doc_sources[doc_id]
        })

    return fused_results
