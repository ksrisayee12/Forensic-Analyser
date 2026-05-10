"""AIVENTRA — Pydantic schemas for /reason endpoint."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ReasonRequest(BaseModel):
    case_id: str = Field(..., description="Case ID to reason over")
    model: Optional[str] = Field(None, description="Specific Ollama model to use")
    multi_model: bool = Field(False, description="Run reasoning on all configured models")


class ReasonResponse(BaseModel):
    case_id: str
    summary: str
    model: str
    report_id: Optional[str] = None
    multi_model_responses: Optional[Dict[str, str]] = None
