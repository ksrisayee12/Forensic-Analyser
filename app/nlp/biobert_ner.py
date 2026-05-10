"""
AIVENTRA — BioBERT Named Entity Recognition (Phase 5)
Extracts forensic and biomedical entities from normalized text.
"""
from __future__ import annotations

from typing import Any, Dict, List

import torch
from transformers import pipeline

from app.core.model_registry import ModelRegistry
from app.utils.gpu_utils import get_device

# BioBERT NER label mapping (standard IOB2 + forensic labels)
FORENSIC_ENTITY_TYPES = {
    "B-DISEASE", "I-DISEASE",
    "B-CHEMICAL", "I-CHEMICAL",
    "B-GENE", "I-GENE",
    "B-SPECIES", "I-SPECIES",
    "B-DNA", "I-DNA",
    "B-RNA", "I-RNA",
    "B-CELL_LINE", "I-CELL_LINE",
    "B-CELL_TYPE", "I-CELL_TYPE",
}

# Map BioBERT labels to forensic entity types
LABEL_MAP = {
    "DISEASE": "INJURY",
    "CHEMICAL": "CHEMICAL",
    "GENE": "ORGAN",
    "SPECIES": "ORGANISM",
    "DNA": "DNA",
    "RNA": "RNA",
    "CELL_LINE": "CELL",
    "CELL_TYPE": "TISSUE",
}

_ner_pipeline = None


def _get_ner_pipeline():
    global _ner_pipeline
    if _ner_pipeline is not None:
        return _ner_pipeline

    tokenizer = ModelRegistry.get("biobert_tokenizer")
    model = ModelRegistry.get("biobert_model")

    if tokenizer is None or model is None:
        return None

    device_id = 0 if get_device() == "cuda" else -1
    _ner_pipeline = pipeline(
        "ner",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=device_id,
    )
    return _ner_pipeline


def extract_entities_biobert(text: str) -> List[Dict[str, Any]]:
    """
    Extract named entities from forensic text using BioBERT.

    Returns:
        List of {entity_type, entity_value, source, confidence}
    """
    if not text or len(text.strip()) < 5:
        return []

    ner = _get_ner_pipeline()
    if ner is None:
        # Fallback: return empty list
        return []

    entities: List[Dict[str, Any]] = []

    # Process in chunks to handle long documents
    max_len = 400
    words = text.split()
    for i in range(0, len(words), max_len):
        chunk = " ".join(words[i: i + max_len])
        try:
            results = ner(chunk)
            for r in results:
                raw_label = r.get("entity_group", r.get("entity", "")).replace("B-", "").replace("I-", "")
                mapped_type = LABEL_MAP.get(raw_label, raw_label)
                word = r.get("word", "").strip()
                score = float(r.get("score", 0.0))
                if word and score > 0.5:
                    entities.append({
                        "entity_type": mapped_type,
                        "entity_value": word,
                        "source": "biobert",
                        "confidence": round(score, 4),
                    })
        except Exception:
            continue

    return entities
