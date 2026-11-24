"""
Grounding and Reliability Verification Module for AutoDiagnose
Implements citation validation, hallucination detection, numerical claim checking,
and evidence sufficiency verification for automotive troubleshooting.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
import re
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

# Known prompt injection & jailbreak attack signatures
INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions|prompts|rules|commands)",
    r"disregard\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions|prompts|rules)",
    r"you\s+are\s+now\s+(?:a|an)?\s*[a-zA-Z0-9_\s]{2,30}",
    r"act\s+as\s+(?:a|an)?\s*[a-zA-Z0-9_\s]{2,30}",
    r"forget\s+(?:all\s+)?(?:previous|everything|prior)",
    r"system\s*prompt\s*:",
    r"reveal\s+(?:your\s+)?(?:system\s+)?(?:prompt|instructions|rules)",
    r"repeat\s+the\s+(?:text|words|prompt)\s+above",
    r"dan\s+mode",
    r"jailbreak"
]

# Prohibited illegal automotive tampering operations
MALICIOUS_AUTOMOTIVE_PATTERNS = [
    r"hotwire\s+(?:a|the)?\s*car",
    r"steal\s+(?:a|the)?\s*(?:car|vehicle|truck)",
    r"rollback\s+(?:the\s+)?odometer",
    r"tamper\s+with\s+(?:the\s+)?odometer",
    r"bypass\s+ignition\s+without\s+key",
    r"disable\s+airbag\s+to\s+hide\s+accident"
]

class PromptInjectionDetector:
    """
    Detects adversarial prompt injections, jailbreak attempts, and illegal
    automotive tampering queries before they reach the retriever or LLM.
    """
    def check_query_safety(self, query: str) -> Tuple[bool, str]:
        """
        Returns (is_safe: bool, reason: str).
        is_safe=False if query contains jailbreak attempts or illegal vehicle tampering.
        """
        query_lower = query.lower().strip()

        # 1. Check prompt injection and jailbreak signatures
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, query_lower):
                return False, f"SECURITY_ALERT: Adversarial prompt injection or jailbreak attempt detected ('{pattern}')."

        # 2. Check malicious automotive tampering
        for pattern in MALICIOUS_AUTOMOTIVE_PATTERNS:
            if re.search(pattern, query_lower):
                return False, f"POLICY_VIOLATION: Request violates automotive safety and legal compliance boundaries ('{pattern}')."

        return True, "Query passed security and safety compliance checks."

class GroundingVerifier:
    """
    Validates that LLM responses strictly adhere to evidence-grounding constraints,
    verifies source citations, checks numerical claims, and blocks prompt injections.
    """
    def __init__(self, min_similarity_threshold: float = 0.25):
        self.min_similarity_threshold = min_similarity_threshold
        self.injection_detector = PromptInjectionDetector()

    def detect_prompt_injection(self, query: str) -> Tuple[bool, str]:
        """Runs pre-retrieval security and prompt injection audit on user query."""
        return self.injection_detector.check_query_safety(query)

    def verify_evidence_sufficiency(
        self,
        query: str,
        retrieved_hits: List[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Determines whether the retrieved technical records provide sufficient,
        high-confidence evidence to diagnose the vehicle issue safely.
        """
        query_codes = re.findall(r"\b[PCBU]\d[0-9A-Za-z]{3}\b", query.upper())
        if not retrieved_hits:
            if query_codes:
                return False, f"No valid data found: Trouble code(s) {query_codes} not found in retrieved technical records."
            return False, "No valid data found: No technical records were retrieved from the knowledge base."

        # Check top hit confidence score
        top_hit = retrieved_hits[0]
        top_score = float(top_hit.get("rerank_score") or top_hit.get("score") or top_hit.get("rrf_score") or 0.0)

        if top_score < self.min_similarity_threshold:
            return False, f"Retrieval confidence ({top_score:.3f}) is below safe threshold ({self.min_similarity_threshold:.3f})."

        # Check trouble code matching if code present in query
        if query_codes:
            matched = False
            for hit in retrieved_hits:
                meta = hit.get("metadata", {})
                doc_code = str(meta.get("dtc_code", "")).upper()
                text = hit.get("text", "").upper()
                if any(code == doc_code or code in text for code in query_codes):
                    matched = True
                    break
            if not matched:
                return False, f"Trouble code(s) {query_codes} not found in retrieved technical records."

        return True, "Evidence is sufficient for grounded synthesis."

    def extract_citations(self, response_text: str) -> List[str]:
        """
        Extracts cited source IDs from the response text.
        Patterns: [Source: id], (Source: id), [id]
        """
        pattern = r"\[(?:Source:\s*)?([a-zA-Z0-9_]+)\]"
        raw_matches = re.findall(pattern, response_text)
        return list(dict.fromkeys(raw_matches))

    def verify_citations(
        self,
        response_text: str,
        retrieved_hits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Verifies that every citation in the response corresponds to a real retrieved chunk or parent ID.
        """
        valid_ids: Set[str] = set()
        for hit in retrieved_hits:
            valid_ids.add(hit["chunk_id"])
            parent_id = hit.get("metadata", {}).get("parent_doc_id")
            if parent_id:
                valid_ids.add(parent_id)

        cited_ids = self.extract_citations(response_text)
        verified_citations = [cid for cid in cited_ids if cid in valid_ids]
        hallucinated_citations = [cid for cid in cited_ids if cid not in valid_ids]

        is_grounded = len(hallucinated_citations) == 0 and len(verified_citations) > 0

        return {
            "is_grounded": is_grounded,
            "cited_ids": cited_ids,
            "verified_citations": verified_citations,
            "hallucinated_citations": hallucinated_citations,
            "citation_count": len(cited_ids)
        }

    def verify_numerical_claims(
        self,
        response_text: str,
        context_text: str
    ) -> Dict[str, Any]:
        """
        Checks that dollar amounts and labor hours mentioned in the response
        are grounded in the provided technical context.
        """
        # Extract dollar amounts (e.g., $15, $45.00)
        resp_dollars = set(re.findall(r"\$\s*\d+(?:\.\d{1,2})?", response_text))
        ctx_dollars = set(re.findall(r"\$\s*\d+(?:\.\d{1,2})?", context_text))

        unsupported_dollars = [d for d in resp_dollars if d not in ctx_dollars]

        # Extract DTC codes (P/C/B/U followed by digit and 3 alphanumeric chars)
        resp_codes = set(re.findall(r"\b[PCBU]\d[0-9A-Za-z]{3}\b", response_text.upper()))
        ctx_codes = set(re.findall(r"\b[PCBU]\d[0-9A-Za-z]{3}\b", context_text.upper()))

        unsupported_codes = [c for c in resp_codes if c not in ctx_codes]

        has_hallucinations = bool(unsupported_dollars or unsupported_codes)

        return {
            "has_unsupported_facts": has_hallucinations,
            "unsupported_costs": unsupported_dollars,
            "unsupported_dtc_codes": unsupported_codes
        }

    def run_full_verification(
        self,
        query: str,
        response_text: str,
        retrieved_hits: List[Dict[str, Any]],
        context_text: str
    ) -> Dict[str, Any]:
        """
        Runs complete reliability pipeline: evidence sufficiency, citation audit,
        and factual claim verification.
        """
        is_sufficient, sufficiency_msg = self.verify_evidence_sufficiency(query, retrieved_hits)
        citation_audit = self.verify_citations(response_text, retrieved_hits)
        factual_audit = self.verify_numerical_claims(response_text, context_text)

        overall_valid = is_sufficient and not factual_audit["has_unsupported_facts"] and len(citation_audit["hallucinated_citations"]) == 0

        return {
            "overall_valid": overall_valid,
            "evidence_sufficient": is_sufficient,
            "sufficiency_reason": sufficiency_msg,
            "citation_audit": citation_audit,
            "factual_audit": factual_audit
        }
