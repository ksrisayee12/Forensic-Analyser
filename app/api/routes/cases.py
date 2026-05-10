"""
AIVENTRA — GET /case/{id} endpoint
Retrieve full case record with all forensic findings.
"""
from __future__ import annotations

from fastapi import APIRouter
from app.api.schemas.case import CaseRecord
from app.database import get_full_case

router = APIRouter()


@router.get("/{case_id}", response_model=CaseRecord, summary="Retrieve full case record")
async def get_case_detail(case_id: str):
    """
    Retrieve a complete forensic case record including:
    - Case metadata
    - All detected injuries
    - Image findings and captions
    - Toxicology records
    - Forensic entities
    - Generated reports
    """
    case = await get_full_case(case_id)

    return CaseRecord(
        id=str(case["id"]),
        filename=case["filename"],
        file_type=case["file_type"],
        status=case["status"],
        created_at=case["created_at"],
        updated_at=case["updated_at"],
        injuries=case.get("injuries", []),
        image_findings=case.get("image_findings", []),
        toxicology=case.get("toxicology", []),
        forensic_entities=case.get("forensic_entities", []),
        reports=case.get("reports", []),
    )
