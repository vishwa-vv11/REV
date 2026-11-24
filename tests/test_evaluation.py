"""
Unit Tests for Phase 6: Quantitative RAG Evaluation & IR Metrics
"""
import unittest
import json
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from evaluation.retrieval_metrics import (
    hit_rate_at_k,
    reciprocal_rank,
    precision_at_k,
    recall_at_k,
    compute_aggregate_ir_metrics
)
from evaluation.ragas_evaluation import RAGEvaluator

class TestEvaluationMetrics(unittest.TestCase):
    def test_hit_rate_at_k(self):
        retrieved = ["doc_A", "doc_B", "doc_C"]
        self.assertEqual(hit_rate_at_k(retrieved, "doc_A", k=1), 1.0)
        self.assertEqual(hit_rate_at_k(retrieved, "doc_B", k=1), 0.0)
        self.assertEqual(hit_rate_at_k(retrieved, "doc_B", k=2), 1.0)
        self.assertEqual(hit_rate_at_k(retrieved, "doc_Z", k=3), 0.0)

    def test_reciprocal_rank(self):
        retrieved = ["doc_A", "doc_B", "doc_C"]
        self.assertEqual(reciprocal_rank(retrieved, "doc_A"), 1.0)
        self.assertEqual(reciprocal_rank(retrieved, "doc_B"), 0.5)
        self.assertEqual(reciprocal_rank(retrieved, "doc_C"), 1.0 / 3.0)
        self.assertEqual(reciprocal_rank(retrieved, "doc_Z"), 0.0)

    def test_precision_and_recall_at_k(self):
        retrieved = ["doc_A", "doc_B", "doc_C", "doc_D"]
        relevant = {"doc_A", "doc_C", "doc_E"}

        # Top 2: doc_A, doc_B -> 1 relevant / 2 = 0.5
        self.assertEqual(precision_at_k(retrieved, relevant, k=2), 0.5)

        # Top 4: doc_A, doc_C -> 2 relevant / 3 total relevant = 2/3
        self.assertAlmostEqual(recall_at_k(retrieved, relevant, k=4), 2.0 / 3.0)

    def test_compute_aggregate_ir_metrics(self):
        eval_cases = [
            {"expected_parent_id": "doc_1", "retrieved_parent_ids": ["doc_1", "doc_2"]},
            {"expected_parent_id": "doc_2", "retrieved_parent_ids": ["doc_3", "doc_2"]}
        ]
        agg = compute_aggregate_ir_metrics(eval_cases, k_values=[1, 2])
        self.assertEqual(agg["hit_rate@1"], 0.5)
        self.assertEqual(agg["hit_rate@2"], 1.0)
        # MRR: (1/1 + 1/2) / 2 = 1.5 / 2 = 0.75
        self.assertEqual(agg["mrr"], 0.75)

    def test_benchmark_qa_json_format(self):
        benchmark_file = config.EVALUATION_DATA_DIR / "benchmark_qa.json"
        self.assertTrue(benchmark_file.exists())
        with open(benchmark_file, "r", encoding="utf-8") as f:
            cases = json.load(f)
        self.assertGreater(len(cases), 5)
        for c in cases:
            self.assertIn("id", c)
            self.assertIn("query", c)
            self.assertIn("should_abstain", c)

    def test_faithfulness_evaluation(self):
        evaluator = RAGEvaluator()
        context = "The ignition coil for code P0301 costs $30.00."
        faithful_resp = "Code P0301 coil costs $30.00."
        unfaithful_resp = "Code P9999 coil costs $999.00."

        score_faithful = evaluator.evaluate_faithfulness(faithful_resp, context)
        score_unfaithful = evaluator.evaluate_faithfulness(unfaithful_resp, context)

        self.assertEqual(score_faithful, 1.0)
        self.assertEqual(score_unfaithful, 0.0)

if __name__ == "__main__":
    unittest.main()
