"""
AIVENTRA — BGE-Large Embedding Engine (Phase 10)
Generates dense semantic embeddings for forensic text chunks.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from app.core.model_registry import ModelRegistry
from app.config import settings


def embed_chunks(chunks: List[str], batch_size: int = 32) -> List[Dict[str, Any]]:
    """
    Generate BGE-large embeddings for a list of text chunks.

    Returns:
        List of {
            "text": str,
            "embedding": List[float],   # 1024-dim vector
            "model_used": str,
        }
    """
    model = ModelRegistry.get("bge")
    if model is None or not chunks:
        # Return zero-vectors as fallback
        dim = settings.EMBEDDING_DIMENSION
        return [{"text": c, "embedding": [0.0] * dim, "model_used": "fallback"} for c in chunks]

    results: List[Dict[str, Any]] = []

    # BGE-large requires a query prefix for retrieval tasks
    prefixed = [f"Represent this forensic document for retrieval: {c}" for c in chunks]

    for i in range(0, len(prefixed), batch_size):
        batch_texts = prefixed[i: i + batch_size]
        batch_originals = chunks[i: i + batch_size]

        embeddings = model.encode(
            batch_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=batch_size,
        )

        for text, emb in zip(batch_originals, embeddings):
            results.append({
                "text": text,
                "embedding": emb.tolist(),
                "model_used": "bge-large",
            })

    return results


def embed_query(query: str) -> List[float]:
    """
    Embed a single retrieval query using BGE-large.
    Uses the standard BGE query prefix.
    """
    model = ModelRegistry.get("bge")
    if model is None:
        return [0.0] * settings.EMBEDDING_DIMENSION

    prefixed = f"Represent this forensic query for retrieving relevant documents: {query}"
    emb = model.encode([prefixed], normalize_embeddings=True, show_progress_bar=False)
    return emb[0].tolist()
