"""
Unit Tests for Phase 4: Advanced Retrieval Optimization
Tests BM25 lexical search, RRF rank fusion, MMR diversity, Multi-Query expansion,
Diagnostic Reranking, and Master Hybrid Search.
"""
import unittest
import numpy as np
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.chunking import Chunk
from retrieval.bm25_search import BM25Retriever, tokenize_automotive_text
from retrieval.rrf import reciprocal_rank_fusion
from retrieval.mmr import compute_mmr
from retrieval.multi_query import MultiQueryExpander
from retrieval.reranker import DiagnosticReranker
from retrieval.parent_child import ParentChildResolver
from retrieval.hybrid_search import HybridRetriever

class TestAdvancedRetrieval(unittest.TestCase):
    def test_tokenize_automotive_text(self):
        text = "The car set DTC P0301 with an open MAF and O2 sensor circuit on the highway."
        tokens = tokenize_automotive_text(text)
        self.assertIn("p0301", tokens)
        self.assertIn("maf", tokens)
        self.assertIn("o2", tokens)
        self.assertIn("dtc", tokens)
        self.assertNotIn("the", tokens)
        self.assertNotIn("with", tokens)
        self.assertNotIn("an", tokens)

    def test_bm25_search(self):
        chunks = [
            Chunk("c1", "p1", 0, "Left front wheel speed sensor circuit failure C0031.", 50, 12, {"dtc_code": "C0031"}),
            Chunk("c2", "p2", 0, "Mass air flow MAF sensor circuit performance P0101.", 50, 12, {"dtc_code": "P0101"}),
            Chunk("c3", "p3", 0, "Cylinder 1 misfire detected P0301 with rough idling.", 50, 12, {"dtc_code": "P0301"})
        ]
        bm25 = BM25Retriever()
        bm25.fit(chunks)
        hits = bm25.search("P0301 misfire", top_k=2)
        self.assertGreater(len(hits), 0)
        self.assertEqual(hits[0]["chunk_id"], "c3")
        self.assertGreater(hits[0]["score"], 0.0)

    def test_rrf_scoring(self):
        list1 = [
            {"chunk_id": "docA", "text": "A", "metadata": {}},
            {"chunk_id": "docB", "text": "B", "metadata": {}}
        ]
        list2 = [
            {"chunk_id": "docA", "text": "A", "metadata": {}},
            {"chunk_id": "docC", "text": "C", "metadata": {}}
        ]
        fused = reciprocal_rank_fusion([list1, list2], k_constant=60, top_k=3)
        self.assertEqual(fused[0]["chunk_id"], "docA")
        # docA appears at rank 1 in both lists -> 1/61 + 1/61 = 2/61 ~= 0.0328
        self.assertAlmostEqual(fused[0]["rrf_score"], 2.0 / 61.0, places=4)

    def test_diagnostic_reranker(self):
        reranker = DiagnosticReranker()
        candidates = [
            {"chunk_id": "c1", "text": "General misfire troubleshooting.", "score": 0.8, "metadata": {"dtc_code": "P0300"}},
            {"chunk_id": "c2", "text": "Cylinder 1 misfire detected.", "score": 0.6, "metadata": {"dtc_code": "P0301"}}
        ]
        reranked = reranker.rerank(query="What causes P0301 code?", candidates=candidates, top_k=2)
        # c2 has exact DTC code match and should be boosted to rank 1
        self.assertEqual(reranked[0]["chunk_id"], "c2")
        self.assertTrue(reranked[0]["code_match"])

    def test_multi_query_expansion(self):
        expander = MultiQueryExpander()
        variants = expander.expand("MAF sensor reading is out of range")
        self.assertGreater(len(variants), 1)
        self.assertTrue(any("mass air flow" in v.lower() for v in variants))

    def test_parent_child_resolver(self):
        resolver = ParentChildResolver()
        if resolver.parent_docs:
            sample_parent_id = next(iter(resolver.parent_docs.keys()))
            sample_hit = [{"chunk_id": f"{sample_parent_id}__chunk_0", "text": "sample", "metadata": {}}]
            resolved = resolver.resolve(sample_hit)
            self.assertEqual(len(resolved), 1)
            self.assertEqual(resolved[0]["parent_id"], sample_parent_id)

    def test_hybrid_search_end_to_end(self):
        hybrid = HybridRetriever()
        res = hybrid.search("P0301 cylinder 1 misfire", top_k=3)
        self.assertIn("top_hits", res)
        self.assertGreater(len(res["top_hits"]), 0)
        self.assertGreater(res["vector_count"], 0)
        self.assertGreater(res["bm25_count"], 0)

if __name__ == "__main__":
    unittest.main()
