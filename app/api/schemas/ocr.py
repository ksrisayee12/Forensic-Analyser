"""AIVENTRA — Pydantic schemas for /ocr endpoint."""
from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class OCRBlock(BaseModel):
    text: str
    confidence: float
    bbox: Any = None
    source: str = "paddleocr"


class OCRResponse(BaseModel):
    text: str
    blocks: List[OCRBlock] = []
    confidence: float
    page_count: int = 1
