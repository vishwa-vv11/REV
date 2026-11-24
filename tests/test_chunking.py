"""
Unit Tests for Phase 2: Section-Aware Chunking & Embedding Pipeline
"""
import unittest
import json
import numpy as np
from pathlib import Path
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.chunking import AutomotiveChunker, Chunk

class TestChunkingAndEmbeddings(unittest.TestCase):
    def setUp(self):
        self.chunker = AutomotiveChunker(chunk_size=200, chunk_overlap=30)

    def test_recursive_split_short_text(self):
        text = "Short automotive troubleshooting note."
        chunks = self.chunker.recursive_split_text(text)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], text)

    def test_recursive_split_long_text(self):
        text = (
            "The check engine light illuminated on the dashboard. "
            "The technician connected the OBD-II scan tool and retrieved trouble code P0301. "
            "P0301 indicates a cylinder 1 misfire condition detected by the ECM. "
            "Possible causes include a bad spark plug, faulty ignition coil, or clogged fuel injector. "
            "Testing ignition coil resistance is recommended before replacement."
        )
        splits = self.chunker.recursive_split_text(text)
        self.assertGreater(len(splits), 1)
        for s in splits:
            # Each chunk should respect the chunk_size threshold (within margin of word boundaries)
            self.assertLessEqual(len(s), 230)

    def test_markdown_section_split(self):
        markdown_text = (
            "# Main Title\nOverview text\n\n"
            "## Section 1\nContent of section 1\n\n"
            "### Section 1.1\nSub content\n"
        )
        sections = self.chunker.split_by_markdown_sections(markdown_text)
        self.assertEqual(len(sections), 3)
        self.assertTrue(sections[0].startswith("# Main Title"))
        self.assertTrue(sections[1].startswith("## Section 1"))
        self.assertTrue(sections[2].startswith("### Section 1.1"))

    def test_chunk_document_metadata_preservation(self):
        sample_doc = {
            "doc_id": "test_doc_001",
            "content": "## Diagnostic Overview\nEngine vibrates at idle.\n\n### Fix Procedure\nSwap coil.",
            "metadata": {
                "dtc_code": "P0301",
                "system_category": "Powertrain",
                "is_oem_specific": False,
                "oem_make": "Generic"
            }
        }
        chunks = self.chunker.chunk_document(sample_doc)
        self.assertGreater(len(chunks), 0)
        for idx, c in enumerate(chunks):
            self.assertEqual(c.parent_doc_id, "test_doc_001")
            self.assertEqual(c.chunk_index, idx)
            self.assertEqual(c.metadata["dtc_code"], "P0301")
            self.assertEqual(c.metadata["system_category"], "Powertrain")
            self.assertIn("[Powertrain | DTC P0301]", c.text)

    def test_chunks_jsonl_output(self):
        self.assertTrue(config.CHUNKS_JSONL.exists(), "chunks.jsonl missing")
        with open(config.CHUNKS_JSONL, "r", encoding="utf-8") as f:
            first_line = f.readline()
            self.assertTrue(len(first_line.strip()) > 0)
            chunk_dict = json.loads(first_line)
            self.assertIn("chunk_id", chunk_dict)
            self.assertIn("text", chunk_dict)
            self.assertIn("metadata", chunk_dict)

if __name__ == "__main__":
    unittest.main()
