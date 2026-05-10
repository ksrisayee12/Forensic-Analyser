"""
AIVENTRA — Layout Detection (Phase 3)
LayoutLMv3 + Detectron2 for structured forensic document region detection.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np
from PIL import Image

from app.core.model_registry import ModelRegistry


# Forensic-relevant layout label mapping
LAYOUT_LABELS = {
    0: "text",
    1: "title",
    2: "table",
    3: "figure",
    4: "handwritten_note",
    5: "body_diagram",
    6: "wound_annotation",
    7: "signature",
    8: "metadata",
    9: "trajectory_arrow",
    10: "label",
}


def detect_layout(pil_image: Image.Image) -> Dict[str, Any]:
    """
    Run LayoutLMv3 to detect document regions.

    Returns:
        {
            "regions": List[{
                "label": str,
                "bbox": [x0, y0, x1, y1],
                "confidence": float,
            }],
            "has_body_diagram": bool,
            "has_handwriting": bool,
        }
    """
    extractor = ModelRegistry.get("layoutlmv3_extractor")
    model = ModelRegistry.get("layoutlmv3_model")

    if extractor is None or model is None:
        # Fallback: treat entire image as a single text region
        w, h = pil_image.size
        return {
            "regions": [{"label": "text", "bbox": [0, 0, w, h], "confidence": 1.0}],
            "has_body_diagram": False,
            "has_handwriting": False,
        }

    import torch

    device = next(model.parameters()).device
    encoding = extractor(pil_image, return_tensors="pt")
    tensor_keys = {"input_ids", "attention_mask", "bbox", "pixel_values", "token_type_ids"}
    tensor_encoding = {k: v.to(device) for k, v in encoding.items() if k in tensor_keys and hasattr(v, "to")}

    with torch.no_grad():
        outputs = model(**tensor_encoding)

    logits = outputs.logits.squeeze(0)          # (seq_len, num_labels)
    predictions = torch.argmax(logits, dim=-1)  # (seq_len,)
    confidences = torch.softmax(logits, dim=-1).max(dim=-1).values

    # Map predictions back to image bounding boxes
    boxes = encoding.get("bbox", None)
    regions: List[Dict[str, Any]] = []

    if boxes is not None:
        boxes_np = boxes.squeeze(0).cpu().numpy()
        preds_np = predictions.cpu().numpy()
        conf_np = confidences.cpu().numpy()
        w, h = pil_image.size

        for i, (box, pred, conf) in enumerate(zip(boxes_np, preds_np, conf_np)):
            if int(pred) == 0 and i > 0:
                continue  # skip padding tokens
            label = LAYOUT_LABELS.get(int(pred), "unknown")
            # LayoutLMv3 boxes are normalised to [0, 1000]
            x0 = int(box[0] / 1000 * w)
            y0 = int(box[1] / 1000 * h)
            x1 = int(box[2] / 1000 * w)
            y1 = int(box[3] / 1000 * h)
            regions.append({
                "label": label,
                "bbox": [x0, y0, x1, y1],
                "confidence": float(conf),
            })

    labels_found = {r["label"] for r in regions}
    return {
        "regions": regions,
        "has_body_diagram": "body_diagram" in labels_found,
        "has_handwriting": "handwritten_note" in labels_found,
    }


def crop_region(pil_image: Image.Image, bbox: List[int]) -> Image.Image:
    """Crop a PIL image to the given [x0, y0, x1, y1] bounding box."""
    return pil_image.crop(bbox)
