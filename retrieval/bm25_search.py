"""
BM25 Lexical Retrieval Module for AutoDiagnose
Implements Okapi BM25 from scratch with automotive domain tokenization,
preserving Diagnostic Trouble Codes (DTCs), sensor acronyms, and part identifiers.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import math
import re
import json
import pickle
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.chunking import Chunk

# Basic English stopwords, strictly preserving short automotive acronyms
AUTOMOTIVE_PROTECTED_TERMS: Set[str] = {
    "o2", "maf", "map", "ect", "ecm", "pcm", "iat", "tps", "abs",
    "dtc", "vvt", "mil", "can", "obd", "diy", "pin", "ac", "dc"
}

STANDARD_STOPWORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before",
    "being", "below", "between", "both", "but", "by", "could", "did", "do",
    "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into",
    "is", "it", "its", "itself", "me", "more", "most", "my", "myself", "no",
    "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which",
    "while", "who", "whom", "why", "with", "would", "you", "your"
}

def tokenize_automotive_text(text: str) -> List[str]:
    """
    Tokenizes text while preserving automotive trouble codes (e.g., P0301, C0035, U0100)
    and technical terms with hyphens (e.g., OBD-II, coil-on-plug).
    """
    # Find alphanumeric words, hyphenated technical terms, or standard words
    raw_tokens = re.findall(r"\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*\b", text)
    tokens = []
    for token in raw_tokens:
        clean = token.lower().strip()
        if not clean:
            continue
        # Preserve if protected technical acronym or not in standard stopwords
        if clean in AUTOMOTIVE_PROTECTED_TERMS or (clean not in STANDARD_STOPWORDS and len(clean) > 1):
            tokens.append(clean)
    return tokens

class BM25Retriever:
    """
    From-scratch Okapi BM25 implementation optimized for automotive technical retrieval.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lens: List[int] = []
        self.doc_ids: List[str] = []
        self.chunks_data: List[Dict[str, Any]] = []
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}

    def fit(self, chunks: List[Chunk]):
        """
        Builds the BM25 index from a list of Chunk objects.
        """
        self.corpus_size = len(chunks)
        self.doc_ids = [c.chunk_id for c in chunks]
        self.chunks_data = [c.to_dict() for c in chunks]
        self.doc_lens = []
        self.doc_term_freqs = []
        doc_frequencies: Dict[str, int] = {}

        total_length = 0
        for chunk in chunks:
            tokens = tokenize_automotive_text(chunk.text)
            length = len(tokens)
            self.doc_lens.append(length)
            total_length += length

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.doc_term_freqs.append(tf)

            # Record document frequency for each unique term
            for unique_t in tf.keys():
                doc_frequencies[unique_t] = doc_frequencies.get(unique_t, 0) + 1

        self.avg_doc_len = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

        # Compute Okapi BM25 Inverse Document Frequency (IDF)
        self.idf = {}
        for term, df in doc_frequencies.items():
            # Standard smoothed IDF formula
            self.idf[term] = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)

    def search(self, query: str, top_k: int = config.DEFAULT_TOP_K) -> List[Dict[str, Any]]:
        """
        Executes lexical keyword search and returns top_k ranked candidates with BM25 scores.
        """
        query_tokens = tokenize_automotive_text(query)
        if not query_tokens or self.corpus_size == 0:
            return []

        scores: List[float] = [0.0] * self.corpus_size

        for term in query_tokens:
            if term not in self.idf:
                continue
            term_idf = self.idf[term]

            for doc_idx, tf_dict in enumerate(self.doc_term_freqs):
                f = tf_dict.get(term, 0)
                if f > 0:
                    doc_len = self.doc_lens[doc_idx]
                    denominator = f + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                    numerator = f * (self.k1 + 1.0)
                    scores[doc_idx] += term_idf * (numerator / denominator)

        # Rank documents by score
        ranked_indices = sorted(
            [i for i in range(self.corpus_size) if scores[i] > 0.0],
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        results = []
        for rank, idx in enumerate(ranked_indices, 1):
            chunk = self.chunks_data[idx]
            results.append({
                "rank": rank,
                "chunk_id": self.doc_ids[idx],
                "score": float(scores[idx]),
                "text": chunk["text"],
                "metadata": chunk["metadata"]
            })

        return results

    def save(self, filepath: Path = config.PROCESSED_DATA_DIR / "bm25_index.pkl"):
        """Saves BM25 index state to disk for fast startup."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        state = {
            "k1": self.k1,
            "b": self.b,
            "corpus_size": self.corpus_size,
            "avg_doc_len": self.avg_doc_len,
            "doc_lens": self.doc_lens,
            "doc_ids": self.doc_ids,
            "chunks_data": self.chunks_data,
            "doc_term_freqs": self.doc_term_freqs,
            "idf": self.idf
        }
        with open(filepath, "wb") as f:
            pickle.dump(state, f)

    @classmethod
    def load(cls, filepath: Path = config.PROCESSED_DATA_DIR / "bm25_index.pkl") -> "BM25Retriever":
        """Loads serialized BM25 index state."""
        with open(filepath, "rb") as f:
            state = pickle.load(f)
        instance = cls(k1=state["k1"], b=state["b"])
        instance.corpus_size = state["corpus_size"]
        instance.avg_doc_len = state["avg_doc_len"]
        instance.doc_lens = state["doc_lens"]
        instance.doc_ids = state["doc_ids"]
        instance.chunks_data = state["chunks_data"]
        instance.doc_term_freqs = state["doc_term_freqs"]
        instance.idf = state["idf"]
        return instance

def run_bm25_demo():
    print("=" * 70)
    print("PHASE 4: BM25 LEXICAL RETRIEVAL DEMO")
    print("=" * 70)

    # Load chunks
    with open(config.CHUNKS_JSONL, "r", encoding="utf-8") as f:
        chunks = [Chunk.from_dict(json.loads(line)) for line in f if line.strip()]

    print(f"[*] Building BM25 index over {len(chunks)} chunks...")
    bm25 = BM25Retriever()
    bm25.fit(chunks)
    bm25.save()
    print(f"[+] Index built. Vocab size: {len(bm25.idf)} unique terms. Avg Doc Length: {bm25.avg_doc_len:.1f} tokens.")

    # Test exact alphanumeric code search
    test_queries = [
        "P0301",
        "C0031 wheel speed sensor",
        "P0171 vacuum leak lean fuel"
    ]

    for q in test_queries:
        print(f"\n[*] Query: '{q}' (Top 2 BM25 hits):")
        hits = bm25.search(q, top_k=2)
        for h in hits:
            print(f"  [Rank {h['rank']}] BM25 Score: {h['score']:.4f} | ID: {h['chunk_id']}")
            print(f"    Code: {h['metadata'].get('dtc_code')} | Fix: {h['metadata'].get('fix_title')}")
            print(f"    Text: {h['text'][:120]}...")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    run_bm25_demo()
