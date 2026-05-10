"""
AIVENTRA — YOLOv8 Wound Detection Engine (Phase 7)
Detects wounds, trauma, blood regions, and ballistic entry/exit points.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from PIL import Image

from app.core.model_registry import ModelRegistry

# Wound severity mapping by class name
SEVERITY_MAP = {
    "gunshot_entry": "critical",
    "gunshot_exit": "critical",
    "stab_wound": "severe",
    "laceration": "moderate",
    "bruise": "mild",
    "abrasion": "mild",
    "blood_pool": "critical",
    "trauma_mark": "moderate",
    "burn": "severe",
    "fracture_marker": "severe",
}

# Body location heuristics based on bounding box Y position (relative)
def _infer_body_location(bbox: List[float], img_height: int) -> str:
    y_center = (bbox[1] + bbox[3]) / 2
    frac = y_center / img_height
    if frac < 0.15:
        return "head"
    elif frac < 0.30:
        return "neck/shoulder"
    elif frac < 0.50:
        return "chest/upper torso"
    elif frac < 0.65:
        return "abdomen"
    elif frac < 0.80:
        return "pelvis/hip"
    else:
        return "lower extremities"


def detect_wounds(pil_image: Image.Image, confidence_threshold: float = 0.25) -> List[Dict[str, Any]]:
    """
    Run YOLOv8 wound detection on a PIL image.

    Returns:
        List of detection dicts:
        {
            "class_name": str,
            "confidence": float,
            "bbox": [x1, y1, x2, y2],
            "body_location": str,
            "severity": str,
        }
    """
    yolo = ModelRegistry.get("yolo")
    if yolo is None:
        return []

    img_np = np.array(pil_image.convert("RGB"))
    results = yolo(img_np, verbose=False, conf=confidence_threshold)

    detections: List[Dict[str, Any]] = []
    img_height = img_np.shape[0]

    for result in results:
        if result.boxes is None:
            continue
        for box in result.boxes:
            cls_id = int(box.cls[0])
            class_name = result.names.get(cls_id, f"class_{cls_id}")
            conf = float(box.conf[0])
            xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

            detections.append({
                "class_name": class_name,
                "confidence": round(conf, 4),
                "bbox": [round(v, 2) for v in xyxy],
                "body_location": _infer_body_location(xyxy, img_height),
                "severity": SEVERITY_MAP.get(class_name, "unknown"),
            })

    return sorted(detections, key=lambda x: x["confidence"], reverse=True)
