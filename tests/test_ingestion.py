"""
Unit Tests for Phase 1: Data Ingestion and Preprocessing (unittest-compatible)
"""
import json
import unittest
from pathlib import Path
import sys

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.document_loader import DocumentLoader
from ingestion.preprocessing import format_steps

class TestIngestion(unittest.TestCase):
    def test_raw_files_exist(self):
        self.assertTrue(config.DTC_CODES_CSV.exists(), "dtc_codes.csv missing")
        self.assertTrue(config.DIAGNOSTIC_FIXES_CSV.exists(), "diagnostic_fixes.csv missing")
        self.assertTrue(config.REPLACEMENT_PARTS_CSV.exists(), "replacement_parts.csv missing")
        self.assertTrue(config.COST_METADATA_JSON.exists(), "cost_metadata.json missing")
        self.assertTrue(config.ORDERING_METADATA_JSON.exists(), "ordering_metadata.json missing")

    def test_document_loader(self):
        loader = DocumentLoader()
        dtc_df = loader.load_dtc_codes()
        fixes_df = loader.load_diagnostic_fixes()
        parts_df = loader.load_replacement_parts()

        self.assertEqual(len(dtc_df), 90, f"Expected 90 DTC codes, got {len(dtc_df)}")
        self.assertEqual(len(fixes_df), 326, f"Expected 326 fixes, got {len(fixes_df)}")
        self.assertEqual(len(parts_df), 449, f"Expected 449 replacement parts, got {len(parts_df)}")
        self.assertIn("dtc_code", dtc_df.columns)
        self.assertIn("fix_title", fixes_df.columns)
        self.assertIn("part_name", parts_df.columns)

    def test_relational_integrity(self):
        loader = DocumentLoader()
        dtc_df = loader.load_dtc_codes()
        fixes_df = loader.load_diagnostic_fixes()
        parts_df = loader.load_replacement_parts()

        # No orphan fixes
        orphan_fixes = fixes_df[~fixes_df["code_id"].isin(dtc_df["code_id"])]
        self.assertEqual(len(orphan_fixes), 0, f"Found {len(orphan_fixes)} orphan fixes")

        # No orphan parts
        orphan_parts = parts_df[~parts_df["fix_id"].isin(fixes_df["fix_id"])]
        self.assertEqual(len(orphan_parts), 0, f"Found {len(orphan_parts)} orphan parts")

    def test_format_steps(self):
        raw = "1. Unplug sensor • 2. Inspect connector • 3. Clear code"
        formatted = format_steps(raw)
        self.assertIn("1. Unplug sensor", formatted)
        self.assertIn("2. Inspect connector", formatted)
        self.assertIn("3. Clear code", formatted)
        self.assertNotIn("•", formatted)

    def test_synthesized_documents_output(self):
        self.assertTrue(config.SYNTHESIZED_DOCS_JSONL.exists(), "synthesized_documents.jsonl missing")
        docs = []
        with open(config.SYNTHESIZED_DOCS_JSONL, "r", encoding="utf-8") as f:
            for line in f:
                docs.append(json.loads(line))

        self.assertEqual(len(docs), 416, f"Expected 416 documents, got {len(docs)}")

        # Check parent docs
        parent_docs = [d for d in docs if d["metadata"]["doc_type"] == "dtc_overview"]
        self.assertEqual(len(parent_docs), 90, f"Expected 90 parent guides, got {len(parent_docs)}")

        # Check fix docs
        fix_docs = [d for d in docs if d["metadata"]["doc_type"] == "diagnostic_fix"]
        self.assertEqual(len(fix_docs), 326, f"Expected 326 fix docs, got {len(fix_docs)}")

        for d in docs[:10]:
            self.assertGreater(len(d["content"].strip()), 50)
            self.assertTrue(d["metadata"]["dtc_code"])
            self.assertTrue(d["metadata"]["system_category"])

if __name__ == "__main__":
    unittest.main()
