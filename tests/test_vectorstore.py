"""
Unit Tests for Phase 3: ChromaDB Vector Store, Retriever & Context Builder
"""
import unittest
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from vectorstore.chroma_store import AutomotiveVectorStore, sanitize_metadata_for_chroma
from retrieval.vector_search import VectorRetriever
from generation.context_builder import ContextBuilder
from generation.prompt import GROUNDED_SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

class TestVectorStoreAndRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize VectorStore
        cls.vstore = AutomotiveVectorStore()
        cls.retriever = VectorRetriever(cls.vstore)
        cls.context_builder = ContextBuilder()

    def test_sanitize_metadata_for_chroma(self):
        raw_meta = {
            "dtc_code": "P0301",
            "is_oem": False,
            "parts_list": ["Spark plug", "Coil"],
            "missing_field": None,
            "labor_hours": 1.2
        }
        clean = sanitize_metadata_for_chroma(raw_meta)
        self.assertEqual(clean["dtc_code"], "P0301")
        self.assertEqual(clean["is_oem"], False)
        self.assertEqual(clean["parts_list"], "Spark plug, Coil")
        self.assertNotIn("missing_field", clean)
        self.assertEqual(clean["labor_hours"], 1.2)

    def test_vector_search_returns_hits(self):
        query = "Wheel speed sensor circuit fault"
        hits = self.retriever.search(query=query, top_k=3)
        self.assertGreater(len(hits), 0)
        top = hits[0]
        self.assertIn("rank", top)
        self.assertIn("score", top)
        self.assertIn("chunk_id", top)
        self.assertIn("text", top)
        self.assertIn("metadata", top)
        self.assertGreater(top["score"], 0.0)

    def test_metadata_filtering(self):
        query = "circuit fault"
        chassis_hits = self.retriever.search(
            query=query,
            top_k=5,
            filters={"system_category": "Chassis"}
        )
        self.assertGreater(len(chassis_hits), 0)
        for h in chassis_hits:
            self.assertEqual(h["metadata"].get("system_category"), "Chassis")

    def test_context_builder_chunk_context(self):
        sample_hits = [
            {
                "chunk_id": "test_chunk_1",
                "text": "Inspect ignition coil resistance.",
                "metadata": {"dtc_code": "P0301", "system_category": "Powertrain"}
            }
        ]
        context = self.context_builder.build_chunk_context(sample_hits)
        self.assertIn("[Source: test_chunk_1]", context)
        self.assertIn("P0301", context)
        self.assertIn("Inspect ignition coil resistance", context)

    def test_user_prompt_formatting(self):
        context = "Sample automotive context."
        query = "How to fix P0301?"
        prompt = USER_PROMPT_TEMPLATE.format(context=context, query=query)
        self.assertIn("Sample automotive context.", prompt)
        self.assertIn("How to fix P0301?", prompt)

if __name__ == "__main__":
    unittest.main()
