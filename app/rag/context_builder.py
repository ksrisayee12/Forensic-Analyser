"""
AIVENTRA — RAG Context Builder (Phase 12)
Assembles the LLM context window from retrieved chunks.
"""
from __future__ import annotations

from typing import Any, Dict, List


def build_context(
    retrieved: List[Dict[str, Any]],
    max_chars: int = 8000,
    separator: str = "\n---\n",
) -> str:
    """
    Assemble retrieved forensic chunks into a single context string
    for the LLM prompt.

    Args:
        retrieved: Reranked list of {text, score, rank}.
        max_chars: Maximum total characters for the context window.
        separator: Separator between chunks.

    Returns:
        Formatted context string.
    """
    parts: List[str] = []
    total_chars = 0

    for i, item in enumerate(retrieved):
        chunk = item.get("text", "").strip()
        if not chunk:
            continue

        prefix = f"[Evidence {i + 1} | relevance={item.get('score', 0.0):.3f}]\n"
        block = prefix + chunk

        if total_chars + len(block) + len(separator) > max_chars:
            # Truncate last block to fit
            remaining = max_chars - total_chars - len(separator) - len(prefix)
            if remaining > 50:
                parts.append(prefix + chunk[:remaining] + "…")
            break

        parts.append(block)
        total_chars += len(block) + len(separator)

    return separator.join(parts)


def build_entity_context(entities: List[Dict[str, Any]], max_entities: int = 30) -> str:
    """
    Format extracted forensic entities into a structured context block.
    """
    if not entities:
        return ""

    lines = ["EXTRACTED FORENSIC ENTITIES:"]
    for ent in entities[:max_entities]:
        etype = ent.get("entity_type", "UNKNOWN")
        evalue = ent.get("entity_value", "")
        conf = ent.get("confidence", 0.0)
        lines.append(f"  [{etype}] {evalue} (confidence: {conf:.2f})")

    return "\n".join(lines)
