"""
AIVENTRA — SAM2 Wound Segmentation Engine (Phase 7)
Generates pixel-level segmentation masks for detected wounds.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

from app.core.model_registry import ModelRegistry


def segment_wounds(
    pil_image: Image.Image,
    detections: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Run SAM2 segmentation for each detected wound bounding box.

    Args:
        pil_image: Original PIL image.
        detections: List of YOLOv8 detection dicts with 'bbox' key.

    Returns:
        List of {
            "detection_index": int,
            "mask_rle": dict (Run-Length Encoding),
            "area_px": int,
            "mask_bbox": List[float],
        }
    """
    predictor = ModelRegistry.get("sam2")
    if predictor is None or not detections:
        return []

    img_np = np.array(pil_image.convert("RGB"))

    try:
        predictor.set_image(img_np)
    except Exception:
        return []

    masks_output: List[Dict[str, Any]] = []

    for i, det in enumerate(detections):
        bbox = det.get("bbox")
        if not bbox or len(bbox) != 4:
            continue

        # SAM2 expects [x1, y1, x2, y2] as input_box
        input_box = np.array(bbox, dtype=np.float32)

        try:
            masks, scores, _ = predictor.predict(
                point_coords=None,
                point_labels=None,
                box=input_box[None, :],
                multimask_output=False,
            )

            if masks is not None and len(masks) > 0:
                mask = masks[0].astype(bool)
                area = int(mask.sum())
                # Compute tight bounding box of mask
                rows = np.where(mask.any(axis=1))[0]
                cols = np.where(mask.any(axis=0))[0]
                if len(rows) and len(cols):
                    mask_bbox = [
                        float(cols.min()), float(rows.min()),
                        float(cols.max()), float(rows.max()),
                    ]
                else:
                    mask_bbox = bbox

                masks_output.append({
                    "detection_index": i,
                    "mask_rle": _encode_rle(mask),
                    "area_px": area,
                    "mask_bbox": mask_bbox,
                    "score": float(scores[0]) if scores is not None else 0.0,
                })
        except Exception:
            continue

    return masks_output


def _encode_rle(mask: np.ndarray) -> Dict[str, Any]:
    """Simple Run-Length Encoding for binary masks."""
    flat = mask.flatten()
    rle: List[int] = []
    current = int(flat[0])
    count = 1
    for bit in flat[1:]:
        if int(bit) == current:
            count += 1
        else:
            rle.append(count)
            current = int(bit)
            count = 1
    rle.append(count)
    return {"start": int(flat[0]), "counts": rle, "shape": list(mask.shape)}
