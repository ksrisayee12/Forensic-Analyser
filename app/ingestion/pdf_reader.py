"""
AIVENTRA — PDF Ingestion
Uses PyMuPDF for text extraction and page rendering, pdfplumber for table extraction.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PIL import Image


# Render DPI — 150 is sufficient for PaddleOCR and is 4× faster than 300 DPI.
# Set to 300 only if you need pixel-perfect forensic image quality.
_OCR_DPI: int = 150
_DPI_SCALE: float = _OCR_DPI / 72


def read_pdf(file_path: Path, extract_tables: bool = False) -> Dict[str, Any]:
    """
    Extract text, images, and tables from a PDF.

    Args:
        file_path:      Path to the PDF file.
        extract_tables: If True, also run pdfplumber for table extraction
                        (slower — adds a second full PDF pass). Default: False.

    Returns:
        {
            "text": str,               # Full concatenated text
            "images": List[PIL.Image], # One PIL image per page (150 DPI)
            "tables": List[List],      # Extracted tables (or [] if extract_tables=False)
            "page_count": int,
        }
    """
    import fitz  # PyMuPDF

    all_text: List[str] = []
    page_images: List[Image.Image] = []
    all_tables: List[Any] = []

    # --- Text + page rendering via PyMuPDF (single pass) ---
    mat = fitz.Matrix(_DPI_SCALE, _DPI_SCALE)
    doc = fitz.open(str(file_path))
    for page in doc:
        all_text.append(page.get_text("text"))
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        page_images.append(img)
    doc.close()

    # --- Table extraction via pdfplumber (optional, separate pass) ---
    if extract_tables:
        try:
            import pdfplumber
            with pdfplumber.open(str(file_path)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        all_tables.extend(tables)
        except Exception:
            pass  # Tables are optional

    return {
        "text": "\n".join(all_text),
        "images": page_images,
        "tables": all_tables,
        "page_count": len(page_images),
    }
