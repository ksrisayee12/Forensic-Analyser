"""
AIVENTRA — FAISS Vector Store (Phase 11)
Manages per-case FAISS indices for semantic retrieval.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.config import settings
from app.core.exceptions import VectorStoreError


class FAISSStore:
    """
    Per-case FAISS flat index (L2 + inner product).
    Persisted to disk at: {FAISS_INDEX_DIR}/{case_id}.index
    """

    def __init__(self, case_id: str) -> None:
        self.case_id = case_id
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index_path = Path(settings.FAISS_INDEX_DIR) / f"{case_id}.index"
        self.texts_path = Path(settings.FAISS_INDEX_DIR) / f"{case_id}.texts.npy"
        self._index = None
        self._texts: List[str] = []
        self._load_or_create()

    def _load_or_create(self) -> None:
        try:
            import faiss
        except ImportError:
            raise VectorStoreError("faiss-cpu is not installed. Run: pip install faiss-cpu")

        import faiss

        if self.index_path.exists():
            self._index = faiss.read_index(str(self.index_path))
            if self.texts_path.exists():
                self._texts = np.load(str(self.texts_path), allow_pickle=True).tolist()
        else:
            # Inner-product index on L2-normalised vectors = cosine similarity
            self._index = faiss.IndexFlatIP(self.dimension)
            self._texts = []

    def add(self, embedded: List[Dict[str, Any]]) -> None:
        """
        Add embedded chunks to the FAISS index.

        Args:
            embedded: List of {text, embedding, ...} from bge_embedder.
        """
        if not embedded:
            return

        import faiss

        vectors = np.array([e["embedding"] for e in embedded], dtype=np.float32)
        # L2-normalise for cosine similarity with IP index
        faiss.normalize_L2(vectors)
        self._index.add(vectors)
        self._texts.extend([e["text"] for e in embedded])
        self._save()

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search the FAISS index for the top-k nearest chunks.

        Returns:
            List of {text, score, rank}
        """
        import faiss

        if self._index.ntotal == 0:
            return []

        query_vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_vec)

        k = min(top_k, self._index.ntotal)
        distances, indices = self._index.search(query_vec, k)

        results: List[Dict[str, Any]] = []
        for rank, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:
                continue
            results.append({
                "text": self._texts[idx],
                "score": float(dist),
                "rank": rank + 1,
            })
        return results

    def _save(self) -> None:
        import faiss

        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self.index_path))
        np.save(str(self.texts_path), np.array(self._texts, dtype=object))

    @property
    def count(self) -> int:
        return self._index.ntotal if self._index else 0

    def reset(self) -> None:
        """Clear the index and delete persisted files."""
        import faiss

        self._index = faiss.IndexFlatIP(self.dimension)
        self._texts = []
        for p in (self.index_path, self.texts_path):
            if p.exists():
                p.unlink()
