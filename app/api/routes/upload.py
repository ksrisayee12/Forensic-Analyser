"""
AIVENTRA — POST /upload endpoint
Upload a forensic document (PDF/image) and create a case record.
"""
from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, HTTPException
from app.api.schemas.upload import UploadResponse
from app.config import settings
from app.core.exceptions import FileTooLargeError, UnsupportedFileTypeError
from app.database import create_case
from app.utils.file_utils import is_supported, resolve_extension, save_upload

router = APIRouter()


@router.post("", response_model=UploadResponse, summary="Upload a forensic document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a forensic PDF or image file.

    - Creates a case record in the database.
    - Saves the file to the upload directory.
    - Returns a `case_id` for subsequent analysis calls.
    """
    # Validate file type
    if not is_supported(file.filename or ""):
        raise UnsupportedFileTypeError(
            f"File type not supported: {file.filename}. "
            "Supported: pdf, jpg, jpeg, png, tiff, tif"
        )

    # Read and validate size
    contents = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_bytes:
        raise FileTooLargeError(
            f"File size {len(contents) / 1e6:.1f}MB exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Save file
    file_path = save_upload(contents, file.filename or "unknown.pdf")

    # Create DB case record (store the file path for later analysis)
    file_type = resolve_extension(file.filename or "")
    case = await create_case(
        filename=file.filename or "unknown",
        file_type=file_type,
        file_path=str(file_path),
    )

    return UploadResponse(
        case_id=str(case["id"]),
        filename=case["filename"],
        file_type=case["file_type"],
        status=case["status"],
        message="File uploaded successfully. Use POST /analyze to process this case.",
        created_at=case["created_at"],
    )
