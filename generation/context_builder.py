"""
Context Builder Module for AutoDiagnose
Formats retrieved chunks or parent documents into structured evidence blocks
with source IDs, token budgeting, and deduplication.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import json
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

class ContextBuilder:
    """
    Constructs formatted evidence blocks from retrieved chunks or parent documents.
    """
    def __init__(self, synthesized_docs_path: Path = config.SYNTHESIZED_DOCS_JSONL):
        self.synthesized_docs_path = synthesized_docs_path
        self._parent_docs_cache: Optional[Dict[str, Dict[str, Any]]] = None

    def _load_parent_docs(self) -> Dict[str, Dict[str, Any]]:
        """Loads and caches full synthesized parent documents indexed by doc_id."""
        if self._parent_docs_cache is not None:
            return self._parent_docs_cache

        cache = {}
        if self.synthesized_docs_path.exists():
            with open(self.synthesized_docs_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        doc = json.loads(line)
                        cache[doc["doc_id"]] = doc
        self._parent_docs_cache = cache
        return cache

    def build_chunk_context(
        self,
        retrieved_hits: List[Dict[str, Any]],
        max_chars: int = 4000
    ) -> str:
        """
        Builds context directly from retrieved chunks.
        """
        if not retrieved_hits:
            return "No relevant technical records found."

        context_blocks = []
        total_len = 0

        for hit in retrieved_hits:
            chunk_id = hit["chunk_id"]
            meta = hit.get("metadata", {})
            dtc = meta.get("dtc_code", "UNKNOWN")
            category = meta.get("system_category", "Automotive")
            text = hit["text"]

            meta_details = []
            if meta.get("est_parts_cost_min_usd") is not None and meta.get("est_parts_cost_max_usd") is not None:
                meta_details.append(f"Estimated Cost: ${float(meta['est_parts_cost_min_usd']):.2f} - ${float(meta['est_parts_cost_max_usd']):.2f}")
            if meta.get("est_labor_hours") is not None:
                meta_details.append(f"Labor Hours: {meta['est_labor_hours']} hrs")
            if meta.get("parts_list"):
                parts = meta["parts_list"] if isinstance(meta["parts_list"], str) else ", ".join(meta["parts_list"])
                meta_details.append(f"Parts/Tools: {parts}")

            meta_header = f" | ".join(meta_details)
            meta_line = f"**Metadata:** {meta_header}\n" if meta_details else ""

            block = (
                f"### [Source: {chunk_id}] (DTC: {dtc} | Category: {category})\n"
                f"{meta_line}"
                f"{text}\n"
            )

            if total_len + len(block) > max_chars:
                break

            context_blocks.append(block)
            total_len += len(block)

        return "\n".join(context_blocks)

    def build_parent_context(
        self,
        retrieved_hits: List[Dict[str, Any]],
        max_parents: int = 2,
        max_chars: int = 6000
    ) -> str:
        """
        Small-to-Big Retrieval: Identifies parent documents for retrieved child chunks
        and injects the complete, unabridged parent diagnostic guides.
        """
        parent_docs = self._load_parent_docs()
        seen_parents: Set[str] = set()
        context_blocks = []
        total_len = 0

        for hit in retrieved_hits:
            meta = hit.get("metadata", {})
            parent_id = meta.get("parent_doc_id") or hit["chunk_id"].split("__chunk_")[0]

            if parent_id in seen_parents:
                continue
            seen_parents.add(parent_id)

            parent_doc = parent_docs.get(parent_id)
            if parent_doc:
                content = parent_doc["content"]
                block = f"### [Source: {parent_id}]\n{content}\n"
                if total_len + len(block) > max_chars:
                    break
                context_blocks.append(block)
                total_len += len(block)

            if len(seen_parents) >= max_parents:
                break

        if not context_blocks:
            # Fallback to standard chunk context
            return self.build_chunk_context(retrieved_hits, max_chars=max_chars)

        return "\n".join(context_blocks)
