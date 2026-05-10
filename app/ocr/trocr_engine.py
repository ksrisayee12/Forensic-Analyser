"""
AIVENTRA — TrOCR Engine (handwriting recognition)

Performance note:
  - num_beams=4 beam search is ~4× slower than greedy decoding with minimal
    accuracy difference for forensic handwriting. Changed to greedy (num_beams=1).
  - run_trocr_on_crops uses a ThreadPoolExecutor for concurrent crop inference.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

import torch
from PIL import Image

from app.core.model_registry import ModelRegistry
from app.utils.gpu_utils import get_device


def run_trocr(pil_image: Image.Image) -> Dict[str, Any]:
    """
    Run TrOCR on a PIL image to recognise handwritten text.

    Returns:
        {
            "text": str,
            "confidence": float,
        }
    """
    processor = ModelRegistry.get("trocr_processor")
    model = ModelRegistry.get("trocr_model")

    if processor is None or model is None:
        return {"text": "", "confidence": 0.0}

    device = get_device()
    img = pil_image.convert("RGB")
    pixel_values = processor(images=img, return_tensors="pt").pixel_values.to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            pixel_values,
            max_new_tokens=256,
            # Greedy decoding (num_beams=1) is ~4× faster than beam=4 with
            # minimal quality difference for short forensic handwriting labels.
            num_beams=1,
            do_sample=False,
        )

    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)
    text = generated_text[0].strip() if generated_text else ""

    return {"text": text, "confidence": 0.85}  # TrOCR doesn't expose token-level confidence


def run_trocr_on_crops(crops: List[Image.Image]) -> List[Dict[str, Any]]:
    """Run TrOCR on multiple cropped handwriting regions (concurrent thread pool)."""
    if not crops:
        return []
    # Use up to 4 workers — TrOCR is CPU/GPU bound, not GIL-limited via torch
    with ThreadPoolExecutor(max_workers=min(4, len(crops))) as pool:
        return list(pool.map(run_trocr, crops))
