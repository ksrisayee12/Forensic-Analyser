"""AIVENTRA — Pydantic schemas for /upload endpoint."""
from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime


class UploadResponse(BaseModel):
    case_id: str
    filename: str
    file_type: str
    status: str
    message: str
    created_at: datetime
