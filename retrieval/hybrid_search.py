"""
Master Hybrid Retrieval Engine for AutoDiagnose
Orchestrates Dense Semantic Search, BM25 Lexical Matching, Reciprocal Rank Fusion,
MMR Diversity Filtering, and Cross-Feature Diagnostic Reranking.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import re
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.chunking import Chunk
from retrieval.vector_search import VectorRetriever
from retrieval.bm25_search import BM25Retriever
from retrieval.rrf import reciprocal_rank_fusion
from retrieval.mmr import compute_mmr
from retrieval.reranker import DiagnosticReranker
from retrieval.multi_query import MultiQueryExpander
from retrieval.parent_child import ParentChildResolver
from retrieval.hyde import HyDEGenerator

class HybridRetriever:
    """
    High-precision dual-mode retriever combining dense vector semantics with sparse BM25 keywords.
    """
    def __init__(
        self,
        vector_retriever: Optional[VectorRetriever] = None,
        bm25_retriever: Optional[BM25Retriever] = None
    ):
        self.vector_retriever = vector_retriever or VectorRetriever()
        
        # Initialize or load BM25 index
        bm25_path = config.PROCESSED_DATA_DIR / "bm25_index.pkl"
        if bm25_retriever is not None:
            self.bm25_retriever = bm25_retriever
        elif bm25_path.exists():
            print("[*] Loading cached BM25 index from disk...")
            self.bm25_retriever = BM25Retriever.load(bm25_path)
        else:
            print("[*] Building BM25 index from chunks...")
            with open(config.CHUNKS_JSONL, "r", encoding="utf-8") as f:
                chunks = [Chunk.from_dict(json.loads(line)) for line in f if line.strip()]
            self.bm25_retriever = BM25Retriever()
            self.bm25_retriever.fit(chunks)
            self.bm25_retriever.save(bm25_path)

        self.reranker = DiagnosticReranker()
        self.query_expander = MultiQueryExpander()
        self.hyde_generator = HyDEGenerator()
        self.parent_resolver = ParentChildResolver()

    def search(
        self,
        query: str,
        top_k: int = config.DEFAULT_TOP_K,
        use_multi_query: bool = True,
        use_hyde: bool = True,
        use_reranker: bool = True,
        use_mmr: bool = False,
        resolve_parents: bool = False,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end hybrid retrieval:
        1. Query expansion (acronym resolution) + HyDE (Hypothetical Document Embeddings)
        2. Parallel Dense Vector Search + Sparse BM25 Search
        3. Reciprocal Rank Fusion (RRF)
        4. Optional MMR Diversity Filtering
        5. Cross-Feature Diagnostic Reranking
        6. Optional Parent-Child Context Expansion
        """
        # 1. Multi-Query Expansion & HyDE Synthesis
        query_variants = self.query_expander.expand(query) if use_multi_query else [query]
        hypo_doc = None

        # If user did not provide an explicit alphanumeric DTC code (pure human language),
        # generate a hypothetical technical OEM manual excerpt to bridge the semantic gap
        query_codes = re.findall(r"\b[PCBU]\d[0-9A-Za-z]{3}\b", query.upper())
        if not query_codes and use_hyde:
            hypo_doc = self.hyde_generator.generate(query)
            if hypo_doc and hypo_doc not in query_variants:
                query_variants.append(hypo_doc)

        # 2. Dense Vector Search (Search over query variants)
        candidate_k = top_k * 3
        vector_candidates: List[Dict[str, Any]] = []
        seen_vector_ids = set()

        for q_var in query_variants:
            hits = self.vector_retriever.search(query=q_var, top_k=candidate_k, filters=filters)
            for h in hits:
                if h["chunk_id"] not in seen_vector_ids:
                    seen_vector_ids.add(h["chunk_id"])
                    vector_candidates.append(h)

        # 3. Sparse BM25 Lexical Search (include HyDE technical keywords when available)
        bm25_query = f"{query} {hypo_doc}" if hypo_doc else query
        bm25_candidates = self.bm25_retriever.search(query=bm25_query, top_k=candidate_k)

        # 4. Reciprocal Rank Fusion (RRF)
        fused_hits = reciprocal_rank_fusion(
            ranked_lists=[vector_candidates, bm25_candidates],
            weights=[config.HYBRID_VECTOR_WEIGHT, config.HYBRID_BM25_WEIGHT],
            k_constant=config.RRF_K_CONSTANT,
            top_k=candidate_k
        )

        # 5. DTC Alignment & Pruning Filter
        # If query explicitly targets OBD-II trouble code(s), ensure retrieved records match that code.
        query_codes = re.findall(r"\b[PCBU]\d[0-9A-Za-z]{3}\b", query.upper())
        if query_codes:
            matched_candidates = []
            for hit in fused_hits:
                doc_code = str(hit.get("metadata", {}).get("dtc_code", "")).upper()
                text = hit.get("text", "").upper()
                if any(c == doc_code or c in text for c in query_codes):
                    matched_candidates.append(hit)
            
            if matched_candidates:
                fused_hits = matched_candidates
            else:
                # The requested DTC code is not present in the knowledge base at all.
                # Discard unrelated candidate chunks to prevent cross-code false positives.
                fused_hits = []

        # 6. Diagnostic Reranking (using technical terms from HyDE if available)
        rerank_query = f"{query} {hypo_doc}" if hypo_doc else query
        if use_reranker and fused_hits:
            final_hits = self.reranker.rerank(query=rerank_query, candidates=fused_hits, top_k=top_k)
        else:
            final_hits = fused_hits[:top_k]

        # 7. Optional Parent Context Resolution
        parent_docs = []
        if resolve_parents:
            parent_docs = self.parent_resolver.resolve(final_hits, max_parents=2)

        return {
            "query": query,
            "query_variants": query_variants,
            "hypothetical_document": hypo_doc,
            "top_hits": final_hits,
            "resolved_parents": parent_docs,
            "vector_count": len(vector_candidates),
            "bm25_count": len(bm25_candidates)
        }

def run_hybrid_demo():
    print("=" * 70)
    print("PHASE 4: HYBRID RETRIEVAL DEMO (VECTOR + BM25 + RRF + RERANKER)")
    print("=" * 70)

    hybrid = HybridRetriever()

    test_queries = [
        "P0301 engine misfire vibration",
        "How do I clean or test the MAF sensor?",
        "Car is pulling code C0035 for wheel speed sensor"
    ]

    for q in test_queries:
        print(f"\n[*] Query: \"{q}\"")
        res = hybrid.search(q, top_k=3, resolve_parents=True)
        print(f"  - Vector hits considered: {res['vector_count']} | BM25 hits considered: {res['bm25_count']}")
        print("  - Top Ranked Results:")
        for h in res["top_hits"]:
            meta = h.get("metadata", {})
            print(f"    [Rank {h['rank']}] Rerank Score: {h.get('rerank_score', h.get('rrf_score'))} | ID: {h['chunk_id']}")
            print(f"      Code: {meta.get('dtc_code')} | Title: {meta.get('fix_title', 'Overview')}")
            print(f"      Text: {h['text'][:110]}...")

        if res["resolved_parents"]:
            p = res["resolved_parents"][0]
            print(f"  - Expanded Parent Guide: \"{p['title']}\" (Length: {len(p['content'])} chars)")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    run_hybrid_demo()
