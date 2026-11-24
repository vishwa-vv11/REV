"""
Parent-Child Retrieval Resolver for AutoDiagnose
Implements small-to-big context expansion: maps retrieved child chunks
back to their full parent diagnostic technical guides.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

class ParentChildResolver:
    """
    Expands small retrieved chunks into their complete parent documents for LLM synthesis.
    """
    def __init__(self, synthesized_docs_path: Path = config.SYNTHESIZED_DOCS_JSONL):
        self.synthesized_docs_path = Path(synthesized_docs_path)
        self.parent_docs: Dict[str, Dict[str, Any]] = {}
        self._load_parents()

    def _load_parents(self):
        """Loads parent documents into an in-memory dictionary."""
        if not self.synthesized_docs_path.exists():
            print(f"[!] Warning: Parent documents not found at {self.synthesized_docs_path}")
            return

        with open(self.synthesized_docs_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    doc = json.loads(line)
                    self.parent_docs[doc["doc_id"]] = doc

    def resolve(
        self,
        retrieved_hits: List[Dict[str, Any]],
        max_parents: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Given a list of retrieved chunks, resolves and returns unique parent documents
        annotated with the matched child chunks that triggered their retrieval.
        """
        resolved: List[Dict[str, Any]] = []
        seen_parent_ids = set()

        for hit in retrieved_hits:
            meta = hit.get("metadata", {})
            parent_id = meta.get("parent_doc_id") or hit["chunk_id"].split("__chunk_")[0]

            if parent_id in seen_parent_ids:
                # Append matched chunk info to existing parent hit
                for r in resolved:
                    if r["parent_id"] == parent_id:
                        r["matched_chunks"].append({
                            "chunk_id": hit["chunk_id"],
                            "text": hit["text"]
                        })
                continue

            seen_parent_ids.add(parent_id)
            parent_doc = self.parent_docs.get(parent_id)

            if parent_doc:
                resolved.append({
                    "parent_id": parent_id,
                    "title": parent_doc.get("title", ""),
                    "content": parent_doc.get("content", ""),
                    "metadata": parent_doc.get("metadata", {}),
                    "matched_chunks": [{
                        "chunk_id": hit["chunk_id"],
                        "text": hit["text"]
                    }]
                })

            if len(resolved) >= max_parents:
                break

        return resolved
