"""
AIVENTRA — POST /analyze endpoint
Runs the fast 3-phase forensic analysis pipeline on a case.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.api.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.config import settings
from app.core.fast_pipeline import run_fast_pipeline
from app.database import get_case

router = APIRouter()


@router.post("", response_model=AnalyzeResponse, summary="Run forensic analysis pipeline")
async def analyze_case(request: AnalyzeRequest):
    """
    Trigger the 3-phase forensic AI pipeline for an uploaded case.

    Phases:
        1. Text Extraction  — PyMuPDF (native text) → PaddleOCR (scanned PDF fallback)
        2. Forensic Analysis — SciSpaCy NER + forensic regex patterns
        3. LLM Report       — Ollama LLM grounded in PEX02 Autopsy Manual
    """
    # Verify case exists
    case = await get_case(request.case_id)

    # Locate the uploaded file — use the stored file_path first
    file_path: Path | None = None

    stored_path = case.get("file_path")
    if stored_path and Path(stored_path).exists():
        file_path = Path(stored_path)
    else:
        # Fallback: scan the uploads directory for the most recent matching file
        upload_dir = Path(settings.UPLOAD_DIR)
        if upload_dir.exists():
            candidates = sorted(
                [f for f in upload_dir.iterdir() if f.suffix.lstrip(".") == case["file_type"]],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if candidates:
                file_path = candidates[0]

    if file_path is None or not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"File for case {request.case_id} not found. Please re-upload the document.",
        )

    # Allow model override per-request
    if request.model:
        settings.__dict__["OLLAMA_DEFAULT_MODEL"] = request.model

    result = await run_fast_pipeline(case_id=request.case_id, file_path=file_path)

    return AnalyzeResponse(**result)
