"""
AIVENTRA — Instructor-XL Task-Specific Embeddings (Phase 10)
Generates instruction-tuned embeddings for specialized forensic retrieval tasks.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.core.model_registry import ModelRegistry
from app.config import settings

# Task-specific instruction prefixes for Instructor-XL
INSTRUCTIONS = {
    "injury": "Represent the forensic injury finding for retrieval: ",
    "toxicology": "Represent the toxicology report entry for retrieval: ",
    "trajectory": "Represent the ballistic trajectory description for retrieval: ",
    "general": "Represent the forensic document chunk for retrieval: ",
    "query": "Represent the forensic question for retrieving supporting evidence: ",
}


def embed_with_instruction(
    texts: List[str],
    task: str = "general",
    batch_size: int = 16,
) -> List[Dict[str, Any]]:
    """
    Embed texts using Instructor-XL with a task-specific instruction prefix.

    Args:
        texts: List of text strings to embed.
        task: Task key from INSTRUCTIONS dict.
        batch_size: Encoding batch size.

    Returns:
        List of {text, embedding, model_used, task}
    """
    model = ModelRegistry.get("instructor")
    if model is None or not texts:
        dim = settings.EMBEDDING_DIMENSION
        return [{"text": t, "embedding": [0.0] * dim, "model_used": "fallback", "task": task}
                for t in texts]

    instruction = INSTRUCTIONS.get(task, INSTRUCTIONS["general"])
    instruction_pairs = [[instruction, t] for t in texts]

    results: List[Dict[str, Any]] = []

    for i in range(0, len(instruction_pairs), batch_size):
        batch = instruction_pairs[i: i + batch_size]
        originals = texts[i: i + batch_size]

        embeddings = model.encode(batch, show_progress_bar=False)

        for text, emb in zip(originals, embeddings):
            results.append({
                "text": text,
                "embedding": emb.tolist(),
                "model_used": "instructor-xl",
                "task": task,
            })

    return results


def embed_query_instructor(query: str, task: str = "query") -> List[float]:
    """Embed a single query using Instructor-XL."""
    model = ModelRegistry.get("instructor")
    if model is None:
        return [0.0] * settings.EMBEDDING_DIMENSION

    instruction = INSTRUCTIONS.get(task, INSTRUCTIONS["query"])
    emb = model.encode([[instruction, query]], show_progress_bar=False)
    return emb[0].tolist()
