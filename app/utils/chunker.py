"""
AIVENTRA — Text Chunker for RAG pipelines
"""
from __future__ import annotations

from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[str]:
    """
    Split *text* into overlapping character-level chunks suitable for embedding.

    Args:
        text: The full document text.
        chunk_size: Max characters per chunk.
        chunk_overlap: Number of characters to overlap between adjacent chunks.

    Returns:
        List of chunk strings.
    """
    if not text or chunk_size <= 0:
        return []

    text = text.strip()
    chunks: List[str] = []
    start = 0
    step = max(1, chunk_size - chunk_overlap)

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


def chunk_by_sentences(
    text: str,
    max_sentences: int = 8,
    overlap_sentences: int = 2,
) -> List[str]:
    """
    Sentence-aware chunking — better for preserving medical context.
    Falls back to character chunking if sentence splitting fails.
    """
    try:
        import re
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) <= max_sentences:
            return [text.strip()] if text.strip() else []

        chunks: List[str] = []
        step = max(1, max_sentences - overlap_sentences)
        for i in range(0, len(sentences), step):
            window = sentences[i: i + max_sentences]
            chunks.append(" ".join(window))
        return chunks
    except Exception:
        return chunk_text(text)
