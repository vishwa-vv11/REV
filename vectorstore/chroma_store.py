"""
ChromaDB Vector Store Manager for AutoDiagnose
Handles persistent collection creation, batch embedding, indexing,
and dense semantic vector retrieval with cosine distance.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import chromadb
from chromadb.config import Settings
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from ingestion.chunking import Chunk
from ingestion.embedding import AutomotiveEmbedder

def sanitize_metadata_for_chroma(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    ChromaDB only supports primitive metadata types (str, int, float, bool).
    Converts lists (e.g., parts_list) or None values into compatible formats.
    """
    clean = {}
    for k, v in meta.items():
        if v is None:
            continue
        elif isinstance(v, (str, int, float, bool)):
            clean[k] = v
        elif isinstance(v, list):
            clean[k] = ", ".join(str(item) for item in v)
        else:
            clean[k] = str(v)
    return clean

class AutomotiveVectorStore:
    """
    Persistent ChromaDB manager for indexing and querying automotive document chunks.
    """
    def __init__(
        self,
        persist_dir: Path = config.VECTORSTORE_DIR,
        collection_name: str = config.CHROMA_COLLECTION_NAME,
        embedder: Optional[AutomotiveEmbedder] = None
    ):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedder or AutomotiveEmbedder()

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection with cosine similarity metric
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def count(self) -> int:
        """Returns the total number of indexed vectors in the collection."""
        return self.collection.count()

    def add_chunks(self, chunks: List[Chunk], batch_size: int = 128):
        """
        Computes dense embeddings for chunks and indexes them into ChromaDB in batches.
        """
        total = len(chunks)
        print(f"[*] Indexing {total} chunks into ChromaDB collection '{self.collection_name}'...")

        for i in range(0, total, batch_size):
            batch = chunks[i:i + batch_size]
            batch_ids = [c.chunk_id for c in batch]
            batch_texts = [c.text for c in batch]
            batch_metas = [sanitize_metadata_for_chroma(c.metadata) for c in batch]

            # Generate normalized dense embeddings on GPU/CPU
            batch_embeddings = self.embedder.embed_texts(
                batch_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True
            ).tolist()

            # Upsert into ChromaDB
            self.collection.upsert(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_texts,
                metadatas=batch_metas
            )
            print(f"  -> Indexed batch {i + len(batch)} / {total} chunks")

        print(f"[+] Successfully indexed {self.count()} total vectors in ChromaDB.")

    def query(
        self,
        query_text: str,
        top_k: int = config.DEFAULT_TOP_K,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes semantic vector search for a natural-language query.
        Returns a ranked list of matched documents, similarity scores, and metadata.
        """
        # Embed query text
        query_embedding = self.embedder.embed_query(query_text, normalize_embeddings=True).tolist()

        query_args: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        if where:
            query_args["where"] = where

        results = self.collection.query(**query_args)

        formatted_results = []
        if not results or not results["ids"] or not results["ids"][0]:
            return formatted_results

        ids = results["ids"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        for rank, (chunk_id, doc, meta, distance) in enumerate(zip(ids, docs, metas, distances), 1):
            # ChromaDB cosine distance: distance = 1 - cosine_similarity
            similarity_score = max(0.0, 1.0 - distance)
            formatted_results.append({
                "rank": rank,
                "chunk_id": chunk_id,
                "score": float(similarity_score),
                "distance": float(distance),
                "text": doc,
                "metadata": meta
            })

        return formatted_results

    def reset_collection(self):
        """Clears the collection to allow fresh rebuilding."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"[+] Collection '{self.collection_name}' reset.")

def populate_vector_store():
    print("=" * 70)
    print("PHASE 3: POPULATING CHROMADB VECTOR STORE")
    print("=" * 70)

    # 1. Load chunks from chunks.jsonl
    chunks_path = config.CHUNKS_JSONL
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunks file missing at {chunks_path}. Run Phase 2 first.")

    chunks: List[Chunk] = []
    with open(chunks_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(Chunk.from_dict(json.loads(line)))

    # 2. Initialize Vector Store
    vstore = AutomotiveVectorStore()
    
    # Check if already populated
    current_count = vstore.count()
    if current_count == len(chunks):
        print(f"[*] Collection already fully populated with {current_count} vectors.")
    else:
        vstore.add_chunks(chunks)

    # 3. Test Query
    test_query = "Cylinder 1 misfire engine shaking"
    print(f"\n[*] Executing sample vector search: '{test_query}' (Top 3)")
    hits = vstore.query(test_query, top_k=3)
    for h in hits:
        print(f"\n[Rank {h['rank']}] Score: {h['score']:.4f} | ID: {h['chunk_id']}")
        print(f"  Category: {h['metadata'].get('system_category')} | Code: {h['metadata'].get('dtc_code')}")
        print(f"  Text: {h['text'][:140]}...")

    print("\n" + "=" * 70)

if __name__ == "__main__":
    populate_vector_store()
