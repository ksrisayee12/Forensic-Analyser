"""
AIVENTRA — Image Loader
Handles JPG, PNG, TIFF, and multi-page TIFF ingestion.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PIL import Image


def load_image(file_path: Path) -> Dict[str, Any]:
    """
    Load one or more images from a file (supports multi-page TIFF).

    Returns:
        {
            "text": "",
            "images": List[PIL.Image],  # RGB images
            "tables": [],
            "page_count": int,
        }
    """
    images: List[Image.Image] = []

    with Image.open(str(file_path)) as img:
        # Handle multi-page TIFFs
        try:
            while True:
                images.append(img.convert("RGB").copy())
                img.seek(img.tell() + 1)
        except EOFError:
            pass

    if not images:
        # Single-frame fallback
        with Image.open(str(file_path)) as img:
            images.append(img.convert("RGB").copy())

    return {
        "text": "",
        "images": images,
        "tables": [],
        "page_count": len(images),
    }
