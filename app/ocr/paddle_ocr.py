"""
AIVENTRA — PaddleOCR Engine (printed text)
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from PIL import Image

from app.core.model_registry import ModelRegistry


def run_paddleocr(pil_image: Image.Image) -> Dict[str, Any]:
    """
    Run PaddleOCR on a PIL image.

    Returns:
        {
            "text": str,              # Full concatenated text
            "blocks": List[{
                "text": str,
                "confidence": float,
                "bbox": [[x,y], [x,y], [x,y], [x,y]],
            }],
            "confidence": float,      # Average confidence
        }
    """
    ocr = ModelRegistry.get("paddleocr")

    if ocr is None:
        return {"text": "", "blocks": [], "confidence": 0.0}

    img_np = np.array(pil_image.convert("RGB"))
    results = ocr.ocr(img_np, cls=True)

    blocks: List[Dict[str, Any]] = []
    text_lines: List[str] = []
    confidences: List[float] = []

    if results and results[0]:
        for line in results[0]:
            bbox = line[0]           # 4 corner points
            text, conf = line[1]
            blocks.append({"text": text, "confidence": float(conf), "bbox": bbox})
            text_lines.append(text)
            confidences.append(float(conf))

    avg_conf = float(np.mean(confidences)) if confidences else 0.0
    return {
        "text": "\n".join(text_lines),
        "blocks": blocks,
        "confidence": avg_conf,
    }
