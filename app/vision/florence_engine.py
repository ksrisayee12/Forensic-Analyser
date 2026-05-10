"""
AIVENTRA — Florence-2 Image Understanding Engine (Phase 6)
Generates detailed forensic image captions.
"""
from __future__ import annotations

from typing import Any, Dict

import torch
from PIL import Image

from app.core.model_registry import ModelRegistry
from app.utils.gpu_utils import get_device


# Florence-2 task tokens
TASK_DETAILED_CAPTION = "<DETAILED_CAPTION>"
TASK_REGION_CAPTION = "<REGION_TO_CATEGORY>"
TASK_OCR = "<OCR>"


def caption_image(pil_image: Image.Image, task: str = TASK_DETAILED_CAPTION) -> str:
    """
    Generate a detailed forensic caption for a PIL image using Florence-2.

    Returns:
        Caption string.
    """
    processor = ModelRegistry.get("florence2_processor")
    model = ModelRegistry.get("florence2_model")

    if processor is None or model is None:
        return "Image captioning model not available."

    device = get_device()
    img = pil_image.convert("RGB")

    inputs = processor(text=task, images=img, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=512,
            early_stopping=False,
            do_sample=False,
            num_beams=3,
        )

    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)
    if not generated_text:
        return ""

    parsed = processor.post_process_generation(
        generated_text[0],
        task=task,
        image_size=(img.width, img.height),
    )

    if isinstance(parsed, dict):
        return parsed.get(task, "")
    return str(parsed)


def detect_text_in_image(pil_image: Image.Image) -> str:
    """Use Florence-2's OCR task to extract text from forensic diagrams."""
    return caption_image(pil_image, task=TASK_OCR)
