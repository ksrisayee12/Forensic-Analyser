"""
AIVENTRA — POST /extract endpoint
Run medical NLP entity extraction on raw text.
"""
from __future__ import annotations

import asyncio

from fastapi import APIRouter

from app.api.schemas.extraction import ExtractRequest, ExtractResponse, ForensicEntity
from app.nlp.biobert_ner import extract_entities_biobert
from app.nlp.scispacy_engine import extract_entities_scispacy
from app.nlp.text_normalizer import normalize_text
from app.reasoning.forensic_reasoner import llm_extract_entities

router = APIRouter()


@router.post("", response_model=ExtractResponse, summary="Extract forensic entities from text")
async def extract_entities(request: ExtractRequest):
    """
    Run the full NLP entity extraction pipeline on provided text.

    Models used:
        - Text Normalizer (abbreviation expansion)
        - BioBERT NER
        - SciSpacy NER
        - (Optional) Ollama LLM extraction
    """
    loop = asyncio.get_event_loop()

    normalized = await loop.run_in_executor(None, normalize_text, request.text)
    biobert_ents = await loop.run_in_executor(None, extract_entities_biobert, normalized)
    scispacy_ents = await loop.run_in_executor(None, extract_entities_scispacy, normalized)

    all_entities = biobert_ents + scispacy_ents
    sources = ["biobert", "scispacy"]

    if request.use_llm:
        llm_ents = await llm_extract_entities(normalized, model=request.model)
        all_entities.extend(llm_ents)
        sources.append(f"llm:{request.model or 'default'}")

    # Deduplicate
    seen = set()
    unique_entities = []
    for e in all_entities:
        key = (e.get("entity_type"), e.get("entity_value", "").lower()[:50])
        if key not in seen:
            seen.add(key)
            unique_entities.append(e)

    return ExtractResponse(
        entities=[
            ForensicEntity(
                entity_type=e.get("entity_type", "UNKNOWN"),
                entity_value=e.get("entity_value", ""),
                source=e.get("source", "unknown"),
                confidence=e.get("confidence", 0.0),
            )
            for e in unique_entities
        ],
        entity_count=len(unique_entities),
        sources_used=sources,
    )
