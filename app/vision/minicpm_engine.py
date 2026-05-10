"""
AIVENTRA — MiniCPM-V Wound Interpretation Engine (Phase 6)
Generates forensic wound descriptions from body-map and injury images.
"""
from __future__ import annotations

import torch
from PIL import Image

from app.core.model_registry import ModelRegistry
from app.utils.gpu_utils import get_device

FORENSIC_PROMPT = (
    "You are a forensic pathologist AI assistant. "
    "Analyze this forensic image and describe all visible wounds, injuries, "
    "trauma patterns, blood distribution, and any ballistic or sharp-force indicators. "
    "Be precise, clinical, and objective. Do not speculate beyond what is visible."
)


def interpret_wound_image(pil_image: Image.Image) -> str:
    """
    Use MiniCPM-V to generate a forensic wound interpretation.

    Returns:
        Forensic description string.
    """
    tokenizer = ModelRegistry.get("minicpm_tokenizer")
    model = ModelRegistry.get("minicpm_model")

    if tokenizer is None or model is None:
        return "Wound interpretation model not available."

    device = get_device()
    img = pil_image.convert("RGB")

    # MiniCPM-V uses a specific chat interface
    msgs = [
        {"role": "user", "content": [img, FORENSIC_PROMPT]}
    ]

    try:
        with torch.no_grad():
            result = model.chat(
                image=None,
                msgs=msgs,
                tokenizer=tokenizer,
                max_new_tokens=512,
                sampling=False,
            )
        return str(result).strip()
    except Exception as e:
        return f"Interpretation failed: {e}"


def compare_wound_images(image1: Image.Image, image2: Image.Image) -> str:
    """
    Compare two wound images for trajectory or staging correlation.
    """
    tokenizer = ModelRegistry.get("minicpm_tokenizer")
    model = ModelRegistry.get("minicpm_model")

    if tokenizer is None or model is None:
        return "Model not available."

    compare_prompt = (
        "Compare these two forensic images. Identify whether the wounds are "
        "consistent with the same weapon, trajectory, or mechanism of injury. "
        "Provide a clinical forensic comparison."
    )

    msgs = [
        {"role": "user", "content": [image1, image2, compare_prompt]}
    ]

    try:
        with torch.no_grad():
            result = model.chat(
                image=None,
                msgs=msgs,
                tokenizer=tokenizer,
                max_new_tokens=512,
                sampling=False,
            )
        return str(result).strip()
    except Exception as e:
        return f"Comparison failed: {e}"
