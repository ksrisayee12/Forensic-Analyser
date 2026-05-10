"""
AIVENTRA — ClinicalBERT Text Correction & Normalization (Phase 5)
Uses ClinicalBERT for masked language model-based text correction.
"""
from __future__ import annotations

import re
from typing import List

import torch

from app.core.model_registry import ModelRegistry
from app.utils.gpu_utils import get_device


def correct_clinical_text(text: str, max_corrections: int = 50) -> str:
    """
    Use ClinicalBERT MLM to correct suspicious medical tokens.

    Strategy:
        - Find tokens that look garbled (non-dictionary, short, mixed case)
        - Mask them and let ClinicalBERT predict the most likely replacement
        - Apply top-1 correction if confidence > threshold

    Returns:
        Corrected text string.
    """
    tokenizer = ModelRegistry.get("clinicalbert_tokenizer")
    model = ModelRegistry.get("clinicalbert_model")

    if tokenizer is None or model is None:
        return text

    device = get_device()
    corrected = text
    correction_count = 0

    # Find candidate words to correct (short, uppercase, contain digits mixed with letters)
    candidates = re.findall(r"\b[A-Z]{2,6}\d*\b|\b\w{1,3}\.\b", corrected)
    candidates = list(set(candidates))[:max_corrections]

    for word in candidates:
        if correction_count >= max_corrections:
            break
        # Build a masked sentence around the first occurrence
        idx = corrected.find(word)
        if idx == -1:
            continue
        context_start = max(0, idx - 100)
        context_end = min(len(corrected), idx + len(word) + 100)
        snippet = corrected[context_start:context_end]
        masked = snippet.replace(word, tokenizer.mask_token, 1)

        try:
            inputs = tokenizer(masked, return_tensors="pt", truncation=True, max_length=128)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)

            mask_idx = (inputs["input_ids"][0] == tokenizer.mask_token_id).nonzero(as_tuple=True)[0]
            if len(mask_idx) == 0:
                continue

            logits = outputs.logits[0, mask_idx[0]]
            probs = torch.softmax(logits, dim=-1)
            top_prob, top_id = probs.max(dim=-1)

            if float(top_prob) > 0.7:
                predicted_token = tokenizer.decode([int(top_id)]).strip()
                if predicted_token and predicted_token != word:
                    corrected = corrected.replace(word, predicted_token, 1)
                    correction_count += 1
        except Exception:
            continue

    return corrected
