"""
Information Retrieval (IR) Evaluation Metrics for AutoDiagnose
Implements standard quantitative retrieval evaluation:
Hit Rate@K, Precision@K, Recall@K, and Mean Reciprocal Rank (MRR).
"""
from typing import List, Dict, Any, Optional, Set
import numpy as np

def hit_rate_at_k(retrieved_ids: List[str], target_id: str, k: int = 3) -> float:
    """Returns 1.0 if target_id appears in the top-k retrieved IDs, else 0.0."""
    if not target_id or not retrieved_ids:
        return 0.0
    return 1.0 if target_id in retrieved_ids[:k] else 0.0

def reciprocal_rank(retrieved_ids: List[str], target_id: str) -> float:
    """
    Computes reciprocal rank: 1 / rank of the first relevant document.
    Returns 0.0 if target_id is not in retrieved_ids.
    """
    if not target_id or not retrieved_ids:
        return 0.0
    for rank, doc_id in enumerate(retrieved_ids, 1):
        if doc_id == target_id:
            return 1.0 / rank
    return 0.0

def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 3) -> float:
    """
    Precision@K = |Retrieved@K ∩ Relevant| / K
    """
    if k <= 0 or not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_retrieved / k

def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int = 3) -> float:
    """
    Recall@K = |Retrieved@K ∩ Relevant| / |Relevant|
    """
    if not relevant_ids or not retrieved_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    relevant_retrieved = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_retrieved / len(relevant_ids)

def compute_aggregate_ir_metrics(
    query_eval_results: List[Dict[str, Any]],
    k_values: List[int] = [1, 3, 5]
) -> Dict[str, float]:
    """
    Computes aggregated Mean Hit Rate@K, MRR, Mean Precision@K across multiple queries.
    """
    if not query_eval_results:
        return {}

    metrics: Dict[str, List[float]] = {f"hit_rate@{k}": [] for k in k_values}
    metrics["mrr"] = []

    for item in query_eval_results:
        retrieved = item["retrieved_parent_ids"]
        target = item["expected_parent_id"]

        if target is None:
            continue  # Skip out-of-scope queries for standard retrieval ranking

        metrics["mrr"].append(reciprocal_rank(retrieved, target))
        for k in k_values:
            metrics[f"hit_rate@{k}"].append(hit_rate_at_k(retrieved, target, k=k))

    return {metric: float(np.mean(vals)) if vals else 0.0 for metric, vals in metrics.items()}
