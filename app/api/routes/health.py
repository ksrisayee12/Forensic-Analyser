"""
AIVENTRA — GET /health endpoint
System and model status check.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict

from app.core.model_registry import ModelRegistry
from app.reasoning.ollama_client import ollama
from app.utils.gpu_utils import gpu_memory_stats, get_device

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    device: str
    gpu_memory: Dict[str, Any]
    models_loaded: Dict[str, bool]
    ollama_available: bool
    ollama_models: list


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """System health and model status check."""
    ollama_ok = await ollama.is_available()
    try:
        available_models = await ollama.list_models() if ollama_ok else []
    except Exception:
        available_models = []

    return HealthResponse(
        status="ok",
        device=get_device(),
        gpu_memory=gpu_memory_stats(),
        models_loaded=ModelRegistry.status(),
        ollama_available=ollama_ok,
        ollama_models=available_models,
    )
