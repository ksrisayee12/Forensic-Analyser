"""
AIVENTRA — File Router
Routes uploaded files to the correct ingestion handler.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from app.core.exceptions import UnsupportedFileTypeError
from app.ingestion.pdf_reader import read_pdf
from app.ingestion.image_loader import load_image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff", ".tif"}
PDF_EXTENSIONS = {".pdf"}


def route_file(file_path: Path) -> Dict[str, Any]:
    """
    Inspect the file extension and dispatch to the correct ingestion function.

    Returns:
        {
            "text": str,
            "images": List[PIL.Image],
            "tables": List,
            "page_count": int,
        }
    """
    suffix = file_path.suffix.lower()

    if suffix in PDF_EXTENSIONS:
        return read_pdf(file_path)
    elif suffix in IMAGE_EXTENSIONS:
        return load_image(file_path)
    else:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: '{suffix}'. "
            f"Supported: {PDF_EXTENSIONS | IMAGE_EXTENSIONS}"
        )
