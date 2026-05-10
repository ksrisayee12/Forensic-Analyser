"""AIVENTRA — Pydantic schemas for /extract endpoint."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractRequest(BaseModel):
    text: str = Field(..., description="Normalized forensic text to extract entities from")
    use_llm: bool = Field(False, description="Also run LLM-based entity extraction")
    model: Optional[str] = Field(None, description="Ollama model if use_llm=True")


class ForensicEntity(BaseModel):
    entity_type: str
    entity_value: str
    source: str
    confidence: float


class ExtractResponse(BaseModel):
    entities: List[ForensicEntity] = []
    entity_count: int = 0
    sources_used: List[str] = []
