"""AIVENTRA — Pydantic schemas for /case/{id} endpoint."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class CaseRecord(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    injuries: List[Dict[str, Any]] = []
    image_findings: List[Dict[str, Any]] = []
    toxicology: List[Dict[str, Any]] = []
    forensic_entities: List[Dict[str, Any]] = []
    reports: List[Dict[str, Any]] = []
