"""
Generation & Grounding Quality Evaluator for AutoDiagnose
Calculates Faithfulness, Answer Relevancy, Citation Precision,
and Abstention Accuracy without requiring external cloud LLM dependencies.
"""
from typing import List, Dict, Any, Optional
import numpy as np
import re
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.embedding import AutomotiveEmbedder

class RAGEvaluator:
    """
    Evaluates generation quality along core RAGAS dimensions:
    Faithfulness, Answer Relevancy, Citation Validity, and Safe Abstention.
    """
    def __init__(self, embedder: Optional[AutomotiveEmbedder] = None):
        self.embedder = embedder or AutomotiveEmbedder()

    def evaluate_faithfulness(self, response: str, context: str) -> float:
        """
        Faithfulness: Ratio of extracted factual statements (costs, codes, tools)
        that are strictly grounded in the retrieved context.
        """
        if not response or not context:
            return 0.0

        # Check trouble codes in response (DTC format: P/C/B/U followed by digit and 3 hex/alphanumeric chars)
        resp_codes = set(re.findall(r"\b[PCBU]\d[0-9A-Za-z]{3}\b", response.upper()))
        ctx_codes = set(re.findall(r"\b[PCBU]\d[0-9A-Za-z]{3}\b", context.upper()))

        # Check dollar amounts
        resp_dollars = set(re.findall(r"\$\s*\d+(?:\.\d{1,2})?", response))
        ctx_dollars = set(re.findall(r"\$\s*\d+(?:\.\d{1,2})?", context))

        total_claims = len(resp_codes) + len(resp_dollars)
        if total_claims == 0:
            return 1.0  # No specific quantitative claims made

        grounded_claims = len(resp_codes.intersection(ctx_codes)) + len(resp_dollars.intersection(ctx_dollars))
        return float(grounded_claims / total_claims)

    def evaluate_answer_relevancy(self, query: str, response: str) -> float:
        """
        Answer Relevancy: Cosine similarity between query embedding and response embedding.
        """
        if not query or not response:
            return 0.0
        q_vec = self.embedder.embed_query(query)
        r_vec = self.embedder.embed_query(response[:500])  # Focus on core answer
        sim = self.embedder.cosine_similarity(q_vec, r_vec)
        return float(max(0.0, sim))

    def evaluate_citation_precision(self, verification_dict: Dict[str, Any]) -> float:
        """
        Citation Precision = |Verified Citations| / |Total Citations Cited|
        """
        audit = verification_dict.get("citation_audit", {})
        cited = audit.get("cited_ids", [])
        verified = audit.get("verified_citations", [])
        if not cited:
            return 1.0
        return float(len(verified) / len(cited))

    def evaluate_abstention_accuracy(self, test_records: List[Dict[str, Any]]) -> float:
        """
        Calculates accuracy of abstention decisions on negative/out-of-scope queries.
        """
        negative_cases = [r for r in test_records if r.get("should_abstain")]
        if not negative_cases:
            return 1.0
        correct_abstentions = sum(
            1 for r in negative_cases if not r.get("verification", {}).get("evidence_sufficient", True)
        )
        return float(correct_abstentions / len(negative_cases))
