"""
AIVENTRA — GPU/Device Utilities
"""
from __future__ import annotations

import os
from functools import lru_cache


@lru_cache(maxsize=1)
def get_device() -> str:
    """
    Return the best available compute device string ('cuda', 'mps', 'cpu').
    Respects the DEVICE env var override.
    """
    override = os.getenv("DEVICE", "").strip().lower()
    if override in ("cuda", "cpu", "mps"):
        return override

    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    return "cpu"


def get_torch_dtype():
    """Return the preferred torch dtype for the active device."""
    import torch
    device = get_device()
    return torch.float16 if device == "cuda" else torch.float32


def cuda_device_id() -> int:
    return int(os.getenv("CUDA_DEVICE_ID", "0"))


def gpu_memory_stats() -> dict:
    """Return basic GPU memory stats, or empty dict if CUDA unavailable."""
    try:
        import torch
        if not torch.cuda.is_available():
            return {}
        idx = cuda_device_id()
        return {
            "device": torch.cuda.get_device_name(idx),
            "allocated_gb": round(torch.cuda.memory_allocated(idx) / 1e9, 2),
            "reserved_gb": round(torch.cuda.memory_reserved(idx) / 1e9, 2),
            "total_gb": round(torch.cuda.get_device_properties(idx).total_memory / 1e9, 2),
        }
    except Exception:
        return {}
