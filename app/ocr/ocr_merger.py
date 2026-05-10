"""
AIVENTRA — OCR Merger
Fuses PaddleOCR (printed) and TrOCR (handwriting) results
based on layout region type and confidence scores.
"""
from __future__ import annotations

from typing import Any, Dict, List

from PIL import Image

from app.layout.layout_detector import crop_region
from app.ocr.paddle_ocr import run_paddleocr
from app.ocr.trocr_engine import run_trocr


def run_ocr(pil_image: Image.Image, layout_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the full OCR pipeline for a single page.

    Strategy:
        - Run PaddleOCR on the full image (handles printed text).
        - For regions classified as 'handwritten_note', crop and run TrOCR.
        - Merge results, deduplicate overlapping text.

    Returns:
        {
            "text": str,               # Merged text
            "blocks": List[Dict],      # All text blocks with source
            "confidence": float,
        }
    """
    regions = layout_result.get("regions", [])
    has_handwriting = layout_result.get("has_handwriting", False)

    # --- PaddleOCR (full page) ---
    paddle_result = run_paddleocr(pil_image)
    all_blocks: List[Dict[str, Any]] = [
        {**b, "source": "paddleocr"} for b in paddle_result["blocks"]
    ]
    text_parts: List[str] = [paddle_result["text"]] if paddle_result["text"] else []

    # --- TrOCR on handwritten regions ---
    if has_handwriting:
        hw_regions = [r for r in regions if r["label"] == "handwritten_note"]
        for region in hw_regions:
            try:
                crop = crop_region(pil_image, region["bbox"])
                trocr_result = run_trocr(crop)
                if trocr_result["text"]:
                    all_blocks.append({
                        "text": trocr_result["text"],
                        "confidence": trocr_result["confidence"],
                        "bbox": region["bbox"],
                        "source": "trocr",
                    })
                    text_parts.append(trocr_result["text"])
            except Exception:
                continue

    # --- Merge ---
    merged_text = "\n".join(text_parts)
    avg_conf = (
        sum(b.get("confidence", 0.0) for b in all_blocks) / len(all_blocks)
        if all_blocks else 0.0
    )

    return {
        "text": merged_text,
        "blocks": all_blocks,
        "confidence": round(avg_conf, 4),
    }
