"""
AIVENTRA — POST /ocr endpoint
Run OCR on an uploaded file.

Strategy (fast & reliable):
  1. PyMuPDF text extraction (instant, no image processing)
  2. If no text found (scanned/image PDF), fall back to PaddleOCR serially
     (PaddleOCR is NOT thread-safe — never run concurrently)
"""
from __future__ import annotations

import traceback
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.api.schemas.ocr import OCRBlock, OCRResponse
from app.core.exceptions import OCRError, UnsupportedFileTypeError
from app.utils.file_utils import is_supported, save_upload

router = APIRouter()


@router.post("", response_model=OCRResponse, summary="Run OCR on a forensic document")
async def ocr_document(file: UploadFile = File(...)):
    """
    Extract text from a forensic PDF or image.

    Fast path  : PyMuPDF native text extraction (PDFs with embedded text).
    Fallback   : PaddleOCR for image-only / scanned PDFs (serial, thread-safe).
    """
    if not is_supported(file.filename or ""):
        raise UnsupportedFileTypeError(f"Unsupported file: {file.filename}")

    contents = await file.read()
    file_path = save_upload(contents, file.filename or "ocr_upload.pdf")

    try:
        result = _run_ocr_sync(file_path)
        return OCRResponse(
            text=result["text"],
            blocks=[
                OCRBlock(
                    text=b.get("text", ""),
                    confidence=b.get("confidence", 0.9),
                    bbox=b.get("bbox"),
                    source=b.get("source", "pymupdf"),
                )
                for b in result["blocks"]
            ],
            confidence=round(result["confidence"], 4),
            page_count=result["page_count"],
        )
    except (OCRError, UnsupportedFileTypeError):
        raise
    except Exception as exc:
        tb = traceback.format_exc()
        print(f"[OCR ERROR] {file.filename}\n{tb}")
        raise OCRError(
            message=f"OCR failed for '{file.filename}': {exc}",
            detail=tb.strip().splitlines()[-1],
        ) from exc
    finally:
        file_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Synchronous OCR implementation (runs in thread pool via executor or directly)
# ---------------------------------------------------------------------------

def _run_ocr_sync(file_path: Path) -> dict:
    """
    Extract text from PDF or image synchronously.
    Returns: {text, blocks, confidence, page_count}
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        return _ocr_pdf(file_path)
    else:
        return _ocr_image(file_path)


def _ocr_pdf(path: Path) -> dict:
    """
    PDF OCR:
      1. PyMuPDF text extraction (fast, reliable)
      2. PaddleOCR fallback if no embedded text (scanned PDF)
    """
    import fitz  # PyMuPDF

    doc = fitz.open(str(path))
    pages_text = []
    all_blocks = []
    page_count = len(doc)

    for page_num, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages_text.append(text)
            # Build blocks from PyMuPDF word-level data
            for block in page.get_text("blocks"):
                # block = (x0, y0, x1, y1, "text", block_no, block_type)
                if len(block) >= 5 and block[6] == 0:  # type 0 = text
                    block_text = block[4].strip()
                    if block_text:
                        all_blocks.append({
                            "text": block_text,
                            "confidence": 0.98,
                            "bbox": [block[0], block[1], block[2], block[3]],
                            "source": "pymupdf",
                        })
        else:
            # Scanned page — use PaddleOCR fallback
            paddle_result = _paddle_ocr_page(page)
            pages_text.append(paddle_result["text"])
            all_blocks.extend(paddle_result["blocks"])

    doc.close()

    merged_text = "\n".join(pages_text)
    avg_conf = (
        sum(b["confidence"] for b in all_blocks) / len(all_blocks)
        if all_blocks else 0.9
    )

    return {
        "text": merged_text,
        "blocks": all_blocks,
        "confidence": avg_conf,
        "page_count": page_count,
    }


def _paddle_ocr_page(fitz_page) -> dict:
    """Render one fitz page to PIL and run PaddleOCR serially."""
    try:
        from PIL import Image
        from app.core.model_registry import ModelRegistry

        ocr = ModelRegistry.get("paddleocr")
        if ocr is None:
            return {"text": "", "blocks": []}

        import numpy as np
        mat = __import__("fitz").Matrix(150 / 72, 150 / 72)
        pix = fitz_page.get_pixmap(matrix=mat, colorspace=__import__("fitz").csRGB)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img_np = np.array(img)

        results = ocr.ocr(img_np, cls=True)
        blocks = []
        lines = []

        if results and results[0]:
            for line in results[0]:
                bbox, (text, conf) = line[0], line[1]
                blocks.append({"text": text, "confidence": float(conf), "bbox": bbox, "source": "paddleocr"})
                lines.append(text)

        return {"text": "\n".join(lines), "blocks": blocks}
    except Exception as e:
        print(f"[OCR] PaddleOCR page fallback failed: {e}")
        return {"text": "", "blocks": []}


def _ocr_image(path: Path) -> dict:
    """OCR for standalone image files: PaddleOCR → PIL fallback."""
    try:
        from PIL import Image
        from app.core.model_registry import ModelRegistry
        import numpy as np

        ocr = ModelRegistry.get("paddleocr")
        img = Image.open(str(path)).convert("RGB")

        if ocr is not None:
            results = ocr.ocr(np.array(img), cls=True)
            blocks = []
            lines = []
            if results and results[0]:
                for line in results[0]:
                    bbox, (text, conf) = line[0], line[1]
                    blocks.append({"text": text, "confidence": float(conf), "bbox": bbox, "source": "paddleocr"})
                    lines.append(text)
            avg_conf = sum(b["confidence"] for b in blocks) / len(blocks) if blocks else 0.0
            return {"text": "\n".join(lines), "blocks": blocks, "confidence": avg_conf, "page_count": 1}

    except Exception as e:
        print(f"[OCR] Image OCR failed: {e}")

    return {"text": "", "blocks": [], "confidence": 0.0, "page_count": 1}
