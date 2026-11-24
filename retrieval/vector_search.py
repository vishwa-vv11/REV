"""
Dense Semantic Vector Search Module for AutoDiagnose
Executes similarity search with threshold gating and metadata filtering.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import sys

# Ensure project root is in sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
import config
from vectorstore.chroma_store import AutomotiveVectorStore

class VectorRetriever:
    """
    Retrieves relevant automotive document chunks based on semantic similarity.
    """
    def __init__(self, vector_store: Optional[AutomotiveVectorStore] = None):
        self.vector_store = vector_store or AutomotiveVectorStore()

    def search(
        self,
        query: str,
        top_k: int = config.DEFAULT_TOP_K,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k chunks matching the query, with optional metadata filtering
        and similarity score threshold cutoff.
        """
        results = self.vector_store.query(
            query_text=query,
            top_k=top_k,
            where=filters
        )

        # Apply score threshold filtering
        if score_threshold > 0.0:
            results = [r for r in results if r["score"] >= score_threshold]

        return results

    def search_by_code(
        self,
        query: str,
        dtc_code: str,
        top_k: int = config.DEFAULT_TOP_K
    ) -> List[Dict[str, Any]]:
        """Filters retrieval specifically for a given DTC code."""
        return self.search(query=query, top_k=top_k, filters={"dtc_code": dtc_code.upper()})

    def search_by_category(
        self,
        query: str,
        category: str,
        top_k: int = config.DEFAULT_TOP_K
    ) -> List[Dict[str, Any]]:
        """Filters retrieval specifically for a system category (Powertrain, Chassis, Network)."""
        return self.search(query=query, top_k=top_k, filters={"system_category": category})
