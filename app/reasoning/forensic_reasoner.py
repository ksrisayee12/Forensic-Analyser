"""
AIVENTRA — Forensic Reasoning Engine (Phase 13)
Orchestrates multi-model Ollama reasoning for forensic summarization.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.config import settings
from app.rag.context_builder import build_entity_context
from app.reasoning.ollama_client import ollama
from app.reasoning.prompt_templates import (
    SYSTEM_PROMPT,
    build_forensic_summary_prompt,
    build_rag_query_prompt,
    build_entity_extraction_prompt,
)


async def generate_forensic_summary(
    context: str,
    entities: List[Dict[str, Any]],
    wound_detections: List[Dict[str, Any]],
    spatial_analysis: Dict[str, Any],
    model: str | None = None,
) -> Dict[str, Any]:
    """
    Generate a structured forensic autopsy summary using Ollama.

    Returns:
        {
            "summary": str,      # Structured forensic summary
            "raw_output": str,   # Raw LLM output
            "model": str,
        }
    """
    selected_model = model or settings.OLLAMA_DEFAULT_MODEL
    entity_context = build_entity_context(entities)

    user_prompt = build_forensic_summary_prompt(
        context=context,
        entity_context=entity_context,
        wound_detections=wound_detections,
        spatial_analysis=spatial_analysis,
    )

    raw_output = await ollama.generate(
        prompt=user_prompt,
        model=selected_model,
        system=SYSTEM_PROMPT,
        temperature=0.05,   # Very low temperature for forensic accuracy
        max_tokens=3000,
    )

    return {
        "summary": raw_output.strip(),
        "raw_output": raw_output,
        "model": selected_model,
    }


async def answer_forensic_query(
    query: str,
    context: str,
    model: str | None = None,
) -> Dict[str, Any]:
    """
    Answer a forensic investigator's question using RAG context.

    Returns:
        {
            "answer": str,
            "model": str,
            "query": str,
        }
    """
    selected_model = model or settings.OLLAMA_DEFAULT_MODEL
    prompt = build_rag_query_prompt(query=query, context=context)

    answer = await ollama.generate(
        prompt=prompt,
        model=selected_model,
        system=SYSTEM_PROMPT,
        temperature=0.1,
        max_tokens=1500,
    )

    return {
        "answer": answer.strip(),
        "model": selected_model,
        "query": query,
    }


async def llm_extract_entities(text: str, model: str | None = None) -> List[Dict[str, Any]]:
    """
    Use the LLM to extract structured forensic entities from text.
    Supplements BioBERT + SciSpacy NER.

    Returns:
        List of entity dicts, or [] on parse failure.
    """
    selected_model = model or settings.OLLAMA_DEFAULT_MODEL
    prompt = build_entity_extraction_prompt(text)

    raw = await ollama.generate(
        prompt=prompt,
        model=selected_model,
        system="You are a forensic NLP system. Return only valid JSON.",
        temperature=0.0,
        max_tokens=1000,
    )

    try:
        # Extract JSON array from response (may have markdown code fence)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        entities = json.loads(raw)
        if isinstance(entities, list):
            for ent in entities:
                ent.setdefault("source", f"llm:{selected_model}")
            return entities
    except Exception:
        pass

    return []


async def multi_model_consensus(
    prompt: str,
    models: List[str] | None = None,
) -> Dict[str, Any]:
    """
    Run the same prompt across multiple Ollama models and return all responses.
    Useful for critical forensic decisions requiring multi-model corroboration.

    Returns:
        {
            "responses": {model_name: response},
            "models": List[str],
        }
    """
    target_models = models or settings.available_ollama_models
    responses: Dict[str, str] = {}

    for model in target_models:
        try:
            resp = await ollama.generate(
                prompt=prompt,
                model=model,
                system=SYSTEM_PROMPT,
                temperature=0.05,
                max_tokens=2000,
            )
            responses[model] = resp.strip()
        except Exception as e:
            responses[model] = f"ERROR: {e}"

    return {
        "responses": responses,
        "models": target_models,
    }
