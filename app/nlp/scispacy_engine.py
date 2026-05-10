"""
AIVENTRA — SciSpacy Entity Extraction (Phase 5)
Uses the en_core_sci_lg model for scientific/medical NER and entity linking.
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.core.model_registry import ModelRegistry

# Map SciSpacy entity labels to AIVENTRA forensic types
LABEL_MAP = {
    "ENTITY": "MEDICAL_ENTITY",
    "DISEASE": "INJURY",
    "CHEMICAL": "CHEMICAL",
    "TAXON": "ORGANISM",
    "GENE_OR_GENE_PRODUCT": "ORGAN",
    "SIMPLE_CHEMICAL": "SUBSTANCE",
    "ORGANISM": "ORGANISM",
    "CELLULAR_COMPONENT": "TISSUE",
    "PROTEIN": "PROTEIN",
}


def extract_entities_scispacy(text: str) -> List[Dict[str, Any]]:
    """
    Run SciSpacy NER on forensic/medical text.

    Returns:
        List of {entity_type, entity_value, source, confidence}
    """
    nlp = ModelRegistry.get("scispacy")
    if nlp is None or not text:
        return []

    entities: List[Dict[str, Any]] = []
    max_chars = 100_000  # SciSpacy limit

    # Process in 10k-char windows
    window = 10_000
    for start in range(0, min(len(text), max_chars), window):
        chunk = text[start: start + window]
        try:
            doc = nlp(chunk)
            for ent in doc.ents:
                raw_label = ent.label_
                mapped_label = LABEL_MAP.get(raw_label, raw_label)
                entities.append({
                    "entity_type": mapped_label,
                    "entity_value": ent.text.strip(),
                    "source": "scispacy",
                    "confidence": round(float(ent._.score_doc) if hasattr(ent._, "score_doc") else 0.75, 4),
                })
        except Exception:
            continue

    return entities


def extract_forensic_noun_phrases(text: str) -> List[str]:
    """
    Extract noun phrases likely to be forensic evidence items.
    """
    nlp = ModelRegistry.get("scispacy")
    if nlp is None or not text:
        return []

    doc = nlp(text[:10_000])
    return [chunk.text.strip() for chunk in doc.noun_chunks if len(chunk.text.strip()) > 3]
