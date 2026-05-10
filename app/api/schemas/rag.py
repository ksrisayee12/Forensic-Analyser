"""AIVENTRA — Pydantic schemas for /rag/query endpoint."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    case_id: str = Field(..., description="Case ID to query against")
    query: str = Field(..., description="Forensic investigation question")
    model: Optional[str] = Field(None, description="Ollama model for answering")
    top_k: int = Field(5, ge=1, le=20, description="Number of chunks to retrieve")


class RAGResult(BaseModel):
    text: str
    score: float
    rank: int


class RAGQueryResponse(BaseModel):
    case_id: str
    query: str
    answer: str
    model: str
    retrieved_chunks: List[RAGResult] = []
    chunk_count: int = 0
