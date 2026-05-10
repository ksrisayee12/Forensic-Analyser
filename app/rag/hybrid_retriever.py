"""
AIVENTRA — Hybrid RAG Retriever (Phase 12)
Fuses FAISS semantic retrieval + BM25 lexical retrieval with cross-encoder reranking.
No LangChain — fully hand-rolled.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.config import settings
from app.embedding.bge_embedder import embed_query
from app.rag.bm25_retriever import BM25Retriever
from app.vectorstore.faiss_store import FAISSStore


def hybrid_retrieve(
    query: str,
    faiss_store: FAISSStore,
    corpus: List[str],
    top_k_semantic: int | None = None,
    top_k_bm25: int | None = None,
    top_k_final: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid retrieval:
        1. FAISS semantic search (BGE-large embedding)
        2. BM25 lexical search
        3. Score fusion (Reciprocal Rank Fusion)
        4. Cross-encoder reranking

    Returns:
        Top-k reranked results as List[{text, score, rank}]
    """
    k_sem = top_k_semantic or settings.RAG_TOP_K_SEMANTIC
    k_bm25 = top_k_bm25 or settings.RAG_TOP_K_BM25
    k_final = top_k_final or settings.RAG_TOP_K_RERANK

    # --- Semantic retrieval ---
    query_emb = embed_query(query)
    semantic_results = faiss_store.search(query_emb, top_k=k_sem)

    # --- BM25 retrieval ---
    bm25 = BM25Retriever(corpus)
    bm25_results = bm25.retrieve(query, top_k=k_bm25)

    # --- Reciprocal Rank Fusion (RRF) ---
    fused = _reciprocal_rank_fusion(semantic_results, bm25_results)

    # --- Cross-encoder reranking ---
    reranked = _rerank(query, fused, top_k=k_final)

    return reranked


def _reciprocal_rank_fusion(
    *result_lists: List[Dict[str, Any]],
    k: int = 60,
) -> List[Dict[str, Any]]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion.
    RRF score = Σ 1 / (k + rank_i)
    """
    scores: Dict[str, float] = {}
    texts: Dict[str, str] = {}

    for result_list in result_lists:
        for item in result_list:
            text = item["text"]
            rank = item.get("rank", 1)
            if text not in scores:
                scores[text] = 0.0
                texts[text] = text
            scores[text] += 1.0 / (k + rank)

    sorted_texts = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
    return [
        {"text": t, "score": scores[t], "rank": i + 1}
        for i, t in enumerate(sorted_texts)
    ]


def _rerank(
    query: str,
    candidates: List[Dict[str, Any]],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Cross-encoder reranking using sentence-transformers cross-encoder.
    Falls back to RRF order if cross-encoder not available.
    """
    if not candidates:
        return []

    try:
        from sentence_transformers.cross_encoder import CrossEncoder

        cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        pairs = [(query, c["text"]) for c in candidates]
        scores = cross_encoder.predict(pairs)

        reranked = sorted(
            zip(candidates, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        return [
            {"text": item["text"], "score": float(score), "rank": i + 1}
            for i, (item, score) in enumerate(reranked[:top_k])
        ]

    except Exception:
        # Fallback: return top-k from RRF
        return candidates[:top_k]
