"""
AIVENTRA — BM25 Lexical Retriever (Phase 12)
Implements BM25 keyword-based retrieval using rank-bm25.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from rank_bm25 import BM25Okapi


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words, removing punctuation."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return [t for t in text.split() if len(t) > 1]


class BM25Retriever:
    """
    In-memory BM25 index built over a corpus of text chunks.
    """

    def __init__(self, corpus: List[str]) -> None:
        """
        Args:
            corpus: List of text chunks (same order as FAISS index).
        """
        self.corpus = corpus
        self._tokenized = [_tokenize(doc) for doc in corpus]
        self._bm25 = BM25Okapi(self._tokenized) if self._tokenized else None

    def retrieve(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve top-k chunks by BM25 score.

        Returns:
            List of {text, score, rank}
        """
        if self._bm25 is None or not query:
            return []

        query_tokens = _tokenize(query)
        scores = self._bm25.get_scores(query_tokens)

        # Get top_k indices sorted by score descending
        k = min(top_k, len(self.corpus))
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]

        results: List[Dict[str, Any]] = []
        for rank, idx in enumerate(top_indices):
            if scores[idx] > 0:
                results.append({
                    "text": self.corpus[idx],
                    "score": float(scores[idx]),
                    "rank": rank + 1,
                })
        return results
