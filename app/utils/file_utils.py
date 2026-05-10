"""
AIVENTRA — File Utilities
"""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Optional

from app.config import settings


def save_upload(file_bytes: bytes, original_filename: str) -> Path:
    """
    Save raw upload bytes to the upload directory.
    Returns the full path of the saved file.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    dest = upload_dir / unique_name
    dest.write_bytes(file_bytes)
    return dest


def remove_file(path: Path) -> None:
    """Safely delete a file, ignoring errors."""
    try:
        if path.exists():
            path.unlink()
    except Exception:
        pass


def remove_dir(path: Path) -> None:
    """Safely delete a directory tree."""
    try:
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        pass


def resolve_extension(filename: str) -> str:
    """Return the lowercase file extension without the leading dot."""
    return Path(filename).suffix.lower().lstrip(".")


SUPPORTED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "tiff", "tif"}


def is_supported(filename: str) -> bool:
    return resolve_extension(filename) in SUPPORTED_EXTENSIONS
