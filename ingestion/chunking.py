"""
Chunking Module for AutoDiagnose
Implements Section-Aware and Recursive Character Chunking from scratch,
with diagnostic metadata inheritance and context breadcrumbs.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import re
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config

@dataclass
class Chunk:
    chunk_id: str
    parent_doc_id: str
    chunk_index: int
    text: str
    char_count: int
    token_count_est: int
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Chunk":
        return cls(**data)

class AutomotiveChunker:
    """
    Splits automotive technical documents using section-aware markdown boundaries
    and recursive sub-splitting, preserving diagnostic context and metadata.
    """
    def __init__(
        self,
        chunk_size: int = config.CHUNK_SIZE,
        chunk_overlap: int = config.CHUNK_OVERLAP,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def _split_text_with_separator(self, text: str, separator: str) -> List[str]:
        """Splits text on a separator and retains the separator for continuity."""
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)
        return [s for s in splits if s.strip()]

    def recursive_split_text(self, text: str, separators: Optional[List[str]] = None) -> List[str]:
        """
        Recursively splits text into segments no larger than chunk_size,
        trying progressively smaller separators: paragraph -> line -> sentence -> word.
        """
        text = text.strip()
        if len(text) <= self.chunk_size:
            return [text] if text else []

        seps = separators if separators is not None else self.separators
        if not seps:
            # Fallback hard slice if no separator matches
            return [text[i:i + self.chunk_size] for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

        sep = seps[0]
        remaining_seps = seps[1:]

        if sep not in text:
            return self.recursive_split_text(text, remaining_seps)

        raw_splits = text.split(sep)
        final_chunks: List[str] = []
        current_chunk: List[str] = []
        current_len = 0

        for segment in raw_splits:
            segment_len = len(segment)
            # If a single segment is already larger than chunk_size, recurse with remaining separators
            if segment_len > self.chunk_size:
                if current_chunk:
                    merged = sep.join(current_chunk).strip()
                    if merged:
                        final_chunks.append(merged)
                    current_chunk = []
                    current_len = 0
                sub_splits = self.recursive_split_text(segment, remaining_seps)
                final_chunks.extend(sub_splits)
                continue

            # Check if adding this segment exceeds chunk_size
            additional_len = segment_len + (len(sep) if current_chunk else 0)
            if current_len + additional_len <= self.chunk_size:
                current_chunk.append(segment)
                current_len += additional_len
            else:
                if current_chunk:
                    merged = sep.join(current_chunk).strip()
                    if merged:
                        final_chunks.append(merged)
                    
                    # Handle overlap: keep trailing segments up to chunk_overlap
                    overlap_chunk = []
                    overlap_len = 0
                    for prev_seg in reversed(current_chunk):
                        if overlap_len + len(prev_seg) <= self.chunk_overlap:
                            overlap_chunk.insert(0, prev_seg)
                            overlap_len += len(prev_seg) + len(sep)
                        else:
                            break
                    current_chunk = overlap_chunk
                    current_len = sum(len(s) for s in current_chunk) + (len(sep) * (len(current_chunk) - 1) if current_chunk else 0)

                current_chunk.append(segment)
                current_len += segment_len + (len(sep) if len(current_chunk) > 1 else 0)

        if current_chunk:
            merged = sep.join(current_chunk).strip()
            if merged:
                final_chunks.append(merged)

        return final_chunks

    def split_by_markdown_sections(self, content: str) -> List[str]:
        """
        Splits markdown documents along top-level and procedure headings (#, ##, ###).
        Ensures each section maintains its own conceptual unity.
        """
        # Split on headers while keeping header title
        pattern = r"(?=(?:^|\n)#{1,3}\s+)"
        sections = re.split(pattern, content)
        return [s.strip() for s in sections if s.strip()]

    def chunk_document(self, doc_dict: Dict[str, Any]) -> List[Chunk]:
        """
        Takes an AutomotiveDocument dictionary, breaks it into section-aware chunks,
        injects context breadcrumbs, and enriches each chunk with parent metadata.
        """
        parent_id = doc_dict["doc_id"]
        content = doc_dict["content"]
        parent_meta = dict(doc_dict.get("metadata", {}))
        dtc_code = parent_meta.get("dtc_code", "GENERIC")
        category = parent_meta.get("system_category", "Automotive")

        # Context breadcrumb to anchor semantic embedding even for short steps
        breadcrumb = f"[{category} | DTC {dtc_code}] "

        sections = self.split_by_markdown_sections(content)
        raw_text_chunks: List[str] = []

        for sec in sections:
            if len(sec) <= self.chunk_size:
                raw_text_chunks.append(sec)
            else:
                sub_chunks = self.recursive_split_text(sec)
                raw_text_chunks.extend(sub_chunks)

        chunks: List[Chunk] = []
        for idx, text in enumerate(raw_text_chunks):
            # Prepend breadcrumb if not already present
            chunk_text = text if text.startswith("[") else f"{breadcrumb}{text}"
            
            chunk_meta = dict(parent_meta)
            chunk_meta["chunk_index"] = idx
            chunk_meta["parent_doc_id"] = parent_id
            chunk_meta["total_chunks_in_doc"] = len(raw_text_chunks)

            # Estimate token count (~4 characters per token for English technical text)
            token_est = max(1, len(chunk_text) // 4)

            chunk = Chunk(
                chunk_id=f"{parent_id}__chunk_{idx}",
                parent_doc_id=parent_id,
                chunk_index=idx,
                text=chunk_text,
                char_count=len(chunk_text),
                token_count_est=token_est,
                metadata=chunk_meta
            )
            chunks.append(chunk)

        return chunks

    def process_all(
        self,
        input_path: Path = config.SYNTHESIZED_DOCS_JSONL,
        output_path: Path = config.CHUNKS_JSONL
    ) -> List[Chunk]:
        """Reads synthesized documents, chunks them, and saves to JSONL."""
        if not input_path.exists():
            raise FileNotFoundError(f"Synthesized documents not found at {input_path}. Run preprocessing first.")

        all_chunks: List[Chunk] = []
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                doc_dict = json.loads(line)
                doc_chunks = self.chunk_document(doc_dict)
                all_chunks.extend(doc_chunks)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            for chunk in all_chunks:
                f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")

        print(f"[+] Successfully generated {len(all_chunks)} chunks from {input_path.name}")
        print(f"[+] Saved chunks to: {output_path}")
        return all_chunks

if __name__ == "__main__":
    print("=" * 70)
    print("PHASE 2: SECTION-AWARE & RECURSIVE CHUNKING")
    print("=" * 70)
    chunker = AutomotiveChunker()
    chunks = chunker.process_all()

    # Print summary statistics
    lengths = [c.char_count for c in chunks]
    tokens = [c.token_count_est for c in chunks]
    print(f"\n[+] Chunk Statistics:")
    print(f"  * Total Chunks:        {len(chunks)}")
    print(f"  * Mean Characters:     {sum(lengths)/len(lengths):.1f} chars (min: {min(lengths)}, max: {max(lengths)})")
    print(f"  * Mean Est Tokens:     {sum(tokens)/len(tokens):.1f} tokens (min: {min(tokens)}, max: {max(tokens)})")

    # Sample preview
    print(f"\n[+] Sample Chunk Preview ({chunks[0].chunk_id}):")
    print(f"  * Parent ID: {chunks[0].parent_doc_id}")
    print(f"  * Text:\n    " + "\n    ".join(chunks[0].text[:300].splitlines()))
    print("=" * 70)
