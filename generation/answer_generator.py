"""
Answer Generator Module for AutoDiagnose (Phase 5)
Orchestrates Hybrid Retrieval, Context Construction, Grounded Prompting,
Local Ollama LLM Inference, and Reliability / Hallucination Verification.
"""
from typing import Dict, Any, List, Optional
import json
import urllib.request
import urllib.error
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from retrieval.hybrid_search import HybridRetriever
from generation.context_builder import ContextBuilder
from generation.prompt import GROUNDED_SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from generation.grounding import GroundingVerifier

class AutoDiagnoseGenerator:
    """
    Production-grade evidence-grounded RAG assistant with hallucination guardrails.
    """
    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        context_builder: Optional[ContextBuilder] = None,
        verifier: Optional[GroundingVerifier] = None,
        model_name: str = config.DEFAULT_LLM_MODEL,
        ollama_host: str = config.OLLAMA_HOST
    ):
        self.retriever = retriever or HybridRetriever()
        self.context_builder = context_builder or ContextBuilder()
        self.verifier = verifier or GroundingVerifier()
        self.model_name = model_name
        self.ollama_host = ollama_host

    def check_ollama_status(self) -> bool:
        """Checks if local Ollama server is running and reachable."""
        try:
            req = urllib.request.Request(f"{self.ollama_host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Fetches list of installed models from local Ollama instance."""
        try:
            req = urllib.request.Request(f"{self.ollama_host}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                return models
        except Exception:
            return []

    def query_ollama(
        self,
        prompt: str,
        system_prompt: str = GROUNDED_SYSTEM_PROMPT,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Optional[str]:
        """Calls the local Ollama API to generate a response."""
        chosen_model = model_name or self.model_name
        temp = config.TEMPERATURE if temperature is None else temperature
        url = f"{self.ollama_host}/api/generate"
        payload = {
            "model": chosen_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": temp,
                "num_predict": config.MAX_TOKENS
            }
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result.get("response", "").strip()
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
                err_msg = err_body.get("error", str(e))
            except Exception:
                err_msg = str(e)
            print(f"[!] Ollama HTTP error: {err_msg}")
            return None
        except Exception as e:
            print(f"[!] Ollama error: {e}")
            return None

    def generate_response(
        self,
        query: str,
        use_parent_context: bool = False,
        top_k: int = config.DEFAULT_TOP_K,
        filters: Optional[Dict[str, Any]] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes verified evidence-grounded RAG:
        1. Hybrid Retrieval (Vector + BM25 + RRF + Reranker)
        2. Pre-generation Evidence Sufficiency Check (Abstention guardrail)
        3. Context Construction & Token Budgeting
        4. Grounded Prompt Synthesis
        5. Local LLM Inference (Ollama) with Offline Fallback
        6. Post-generation Grounding & Citation Audit
        """
        # 0. Pre-Retrieval Security & Prompt Injection Audit
        is_safe, safety_msg = self.verifier.detect_prompt_injection(query)
        if not is_safe:
            security_answer = (
                "🚨 **AutoDiagnose Security & Policy Alert**\n\n"
                f"Your inquiry was intercepted and blocked by defensive guardrails:\n"
                f"- **Reason:** {safety_msg}\n"
                "- AutoDiagnose operates under strict safety protocols and cannot execute adversarial prompt injections or requests involving illegal vehicle tampering."
            )
            return {
                "query": query,
                "retrieved_hits": [],
                "context": "",
                "prompt": "",
                "response": security_answer,
                "ollama_active": False,
                "verification": {
                    "overall_valid": False,
                    "evidence_sufficient": False,
                    "is_security_violation": True,
                    "sufficiency_reason": safety_msg,
                    "citation_audit": {"is_grounded": False, "cited_ids": [], "hallucinated_citations": []},
                    "factual_audit": {"has_unsupported_facts": False}
                }
            }

        # 1. Hybrid Retrieval
        search_res = self.retriever.search(
            query=query,
            top_k=top_k,
            use_reranker=True,
            resolve_parents=use_parent_context,
            filters=filters
        )
        hits = search_res["top_hits"]

        # 2. Pre-Generation Evidence Sufficiency Verification
        is_sufficient, sufficiency_msg = self.verifier.verify_evidence_sufficiency(query, hits)

        if not is_sufficient:
            if not hits:
                abstention_answer = (
                    "**No valid data found**\n\n"
                    "**AutoDiagnose Safety Boundary: Insufficient Technical Documentation**\n\n"
                    "No valid data found in the technical knowledge base matching this inquiry.\n"
                    f"- **Reason:** {sufficiency_msg}\n"
                    "- **Guidance:** Please verify the Diagnostic Trouble Code (DTC) or consult the official OEM service manual."
                )
            else:
                abstention_answer = (
                    "**AutoDiagnose Safety Boundary: Insufficient Technical Documentation**\n\n"
                    f"AutoDiagnose cannot safely provide verified repair procedures for this query.\n"
                    f"- **Reason:** {sufficiency_msg}\n"
                    "- **Guidance:** Please verify the Diagnostic Trouble Code (DTC) or consult the official OEM service manual."
                )
            return {
                "query": query,
                "retrieved_hits": hits,
                "context": "",
                "prompt": "",
                "response": abstention_answer,
                "ollama_active": False,
                "verification": {
                    "overall_valid": False,
                    "evidence_sufficient": False,
                    "sufficiency_reason": sufficiency_msg,
                    "citation_audit": {"is_grounded": True, "cited_ids": [], "hallucinated_citations": []},
                    "factual_audit": {"has_unsupported_facts": False}
                }
            }

        # 3. Context Construction
        if use_parent_context and search_res.get("resolved_parents"):
            parent_hits = search_res["resolved_parents"]
            context_blocks = [f"### [Source: {p['parent_id']}]\n{p['content']}" for p in parent_hits]
            context_str = "\n\n".join(context_blocks)
        else:
            context_str = self.context_builder.build_chunk_context(hits)

        # 4. Prompt Construction
        user_prompt = USER_PROMPT_TEMPLATE.format(context=context_str, query=query)

        # 5. LLM Generation
        chosen_model = model_name or self.model_name
        ollama_active = self.check_ollama_status()
        llm_answer = None

        if ollama_active:
            llm_answer = self.query_ollama(
                user_prompt,
                model_name=chosen_model,
                temperature=temperature
            )

        # Deterministic evidence summary if Ollama daemon is offline or failed
        if not llm_answer:
            top_hit = hits[0]
            meta = top_hit.get("metadata", {})
            parts = meta.get("parts_list")
            parts_str = parts if isinstance(parts, str) else ", ".join(parts or []) or "Standard diagnostic tools"
            cost_min = meta.get("est_parts_cost_min_usd", 0.0) or 0.0
            cost_max = meta.get("est_parts_cost_max_usd", 0.0) or 0.0
            cost_str = f"${cost_min:.2f} - ${cost_max:.2f}" if (cost_min or cost_max) else "N/A"

            final_answer = (
                f"### AutoDiagnose Technical Troubleshooting Guidance\n\n"
                f"**Diagnostic Target:** Code `{meta.get('dtc_code', 'N/A')}` ({meta.get('system_category', 'General')})\n"
                f"**Primary Troubleshooting Procedure:** {meta.get('fix_title', 'Diagnostic Inspection')} [Source: {top_hit['chunk_id']}]\n\n"
                f"#### Author Sequence & Difficulty\n"
                f"- **Priority Sequence:** Step {meta.get('probability_rank', '1')} (Authored diagnostic inspection sequence)\n"
                f"- **Difficulty Level:** {meta.get('difficulty_level', 'Standard DIY')}\n"
                f"- **Estimated Labor:** {meta.get('est_labor_hours', 'N/A')} hours\n"
                f"- **Estimated Parts Cost:** {cost_str}\n"
                f"- **Required Parts & Tools:** {parts_str}\n\n"
                f"#### Verified Instructions\n"
                f"{top_hit['text']}\n\n"
                f"> **Safety Disclaimer:** AutoDiagnose identifies probable causes based on technical service records. "
                f"A confirmed diagnosis requires physical multimeter/scan tool verification before replacing components.\n\n"
                f"*(Note: Local Ollama service is currently offline. Start Ollama with `ollama run {chosen_model}` to enable natural-language synthesis.)*"
            )
        else:
            final_answer = llm_answer

        # 6. Post-Generation Verification
        verification = self.verifier.run_full_verification(query, final_answer, hits, context_str)

        return {
            "query": query,
            "retrieved_hits": hits,
            "context": context_str,
            "prompt": user_prompt,
            "response": final_answer,
            "ollama_active": bool(ollama_active and llm_answer),
            "model_name": chosen_model,
            "verification": verification
        }

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 5: EVIDENCE-GROUNDED RAG & RELIABILITY VERIFICATION")
    print("=" * 70)

    rag = AutoDiagnoseGenerator()

    # Test 1: Valid automotive query with known DTC
    query_1 = "My car has code P0301 and shakes at idle. What should I inspect?"
    print(f"\n[*] Test 1: Known Code Query -> \"{query_1}\"")
    res_1 = rag.generate_response(query_1, top_k=2)
    print(f"  - Evidence Sufficient: {res_1['verification']['evidence_sufficient']}")
    print(f"  - Overall Grounding Valid: {res_1['verification']['overall_valid']}")
    print(f"  - Verified Citations: {res_1['verification']['citation_audit']['verified_citations']}")
    print("\n--- Response Preview ---")
    print(res_1["response"][:450] + "...\n")

    # Test 2: Unknown out-of-scope query testing abstention guardrail
    query_2 = "What causes diagnostic error code P9999 on a flying spaceship?"
    print(f"\n[*] Test 2: Out-of-Scope Query -> \"{query_2}\"")
    res_2 = rag.generate_response(query_2)
    print(f"  - Evidence Sufficient: {res_2['verification']['evidence_sufficient']}")
    print(f"  - Abstention Reason: {res_2['verification']['sufficiency_reason']}")
    print("\n--- Response ---")
    print(res_2["response"])

    print("\n" + "=" * 70)
