"""
Cross-Encoder and Diagnostic Reranker Module for AutoDiagnose
Performs fine-grained query-document scoring, alphanumeric DTC boosting,
and procedure rank reordering.
"""
from typing import List, Dict, Any, Optional
import re
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from retrieval.bm25_search import tokenize_automotive_text

class DiagnosticReranker:
    """
    Reranks candidate retrieval hits using cross-feature interaction:
    combines semantic score, exact code matching, query token coverage,
    and diagnostic priority order.
    """
    def __init__(
        self,
        code_boost_weight: float = 0.35,
        token_coverage_weight: float = 0.25,
        base_score_weight: float = 0.40
    ):
        self.code_boost_weight = code_boost_weight
        self.token_coverage_weight = token_coverage_weight
        self.base_score_weight = base_score_weight

    def extract_dtc_codes(self, text: str) -> List[str]:
        """Extracts OBD-II trouble codes (e.g., P0301, C0031, B0001, U0100)."""
        return re.findall(r"\b[PCBU][0-9A-Za-z]{4}\b", text.upper())

    def rerank(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = config.DEFAULT_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Calculates cross-feature reranking score and returns re-ordered candidates.
        """
        if not candidates:
            return []

        query_codes = set(self.extract_dtc_codes(query))
        query_tokens = set(tokenize_automotive_text(query))

        reranked = []
        for orig_rank, item in enumerate(candidates, 1):
            # Use vector similarity score (0.0 to 1.0) if available, or scale RRF score
            if item.get("vector_score") is not None and float(item["vector_score"]) > 0:
                base_score = float(item["vector_score"])
            elif item.get("score") is not None and float(item["score"]) > 0:
                base_score = float(item["score"])
            else:
                raw_rrf = float(item.get("rrf_score", 0.0))
                base_score = min(1.0, raw_rrf * 30.0)

            meta = item.get("metadata", {})
            text = item.get("text", "")
            doc_code = str(meta.get("dtc_code", "")).upper()

            # 1. Exact DTC code matching score
            code_score = 0.0
            if query_codes:
                if doc_code in query_codes or any(c in text.upper() for c in query_codes):
                    code_score = 1.0

            # 2. Query token coverage (what fraction of query terms appear in the chunk)
            coverage_score = 0.0
            if query_tokens:
                doc_tokens = set(tokenize_automotive_text(text))
                intersection = query_tokens.intersection(doc_tokens)
                coverage_score = len(intersection) / len(query_tokens)

            # 3. Priority sequence adjustment (slight preference for authored rank 1, 2)
            prob_rank = meta.get("probability_rank")
            rank_bonus = 0.0
            if prob_rank is not None:
                try:
                    p = int(prob_rank)
                    rank_bonus = max(0.0, (5 - p) * 0.02)  # slight boost for earlier steps
                except ValueError:
                    pass

            # Fused interaction score: adapt weights if query contains no DTC codes
            if not query_codes:
                final_rerank_score = (
                    0.65 * base_score +
                    0.30 * coverage_score +
                    rank_bonus
                )
            else:
                final_rerank_score = (
                    self.base_score_weight * base_score +
                    self.code_boost_weight * code_score +
                    self.token_coverage_weight * coverage_score +
                    rank_bonus
                )

            reranked_item = dict(item)
            reranked_item["original_rank"] = orig_rank
            reranked_item["rerank_score"] = round(final_rerank_score, 4)
            reranked_item["code_match"] = bool(code_score > 0.0)
            reranked.append(reranked_item)

        # Sort by descending rerank score
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

        for new_rank, item in enumerate(reranked[:top_k], 1):
            item["rank"] = new_rank

        return reranked[:top_k]
