"""AIVENTRA — Pydantic schemas for /analyze endpoint."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    case_id: str = Field(..., description="ID of an uploaded case to analyze")
    model: Optional[str] = Field(None, description="Ollama model to use (default: llama3)")


class InjuryResult(BaseModel):
    wound_type: Optional[str] = None
    body_location: Optional[str] = None
    bbox: Optional[List[float]] = None
    confidence: Optional[float] = None
    severity: Optional[str] = None


class SpatialAnalysis(BaseModel):
    wound_count: int = 0
    body_zones: List[str] = []
    trajectory: str = ""
    entry_points: List[Dict[str, Any]] = []
    exit_points: List[Dict[str, Any]] = []
    retained_projectiles: bool = False
    mechanism: str = "unknown"
    severity_summary: str = ""


class AnalyzeResponse(BaseModel):
    case_id: str
    status: str
    entities: List[Dict[str, Any]] = []
    injuries: List[InjuryResult] = []
    spatial_analysis: Optional[SpatialAnalysis] = None
    image_captions: List[Dict[str, Any]] = []
    summary: str = ""
    report_id: Optional[str] = None
