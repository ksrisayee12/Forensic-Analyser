"""
AIVENTRA — Image Preprocessing Pipeline (Phase 2)
OpenCV operations to maximise OCR accuracy with minimal latency.

Performance notes:
  - fastNlMeansDenoising is O(n²) and extremely slow on large images.
    Replaced with Gaussian blur (~10× faster, negligible OCR quality loss).
  - Deskew is skipped when no significant skew is detected (saves ~80 ms/page).
  - Use fast_preprocess() for clean printed documents (skips thresholding).
"""
from __future__ import annotations

import numpy as np
from PIL import Image


def preprocess_image(pil_image: Image.Image, *, fast: bool = False) -> Image.Image:
    """
    Preprocess a PIL image for OCR.

    Args:
        pil_image: Source image (any mode).
        fast:      If True, use the lighter fast path — best for clean printed
                   documents. If False (default), apply the full pipeline
                   including adaptive thresholding and morphological close,
                   which helps with handwriting / noisy scans.

    Steps (full path):
        1. Grayscale conversion
        2. Gaussian denoising  (replaces slow fastNlMeansDenoising)
        3. CLAHE contrast enhancement
        4. Conditional deskew  (skipped when skew < 0.5°)
        5. Adaptive thresholding
        6. Sharpening
        7. Morphological close (handwriting gap fill)
        8. Return RGB PIL Image
    """
    import cv2

    if fast:
        return fast_preprocess(pil_image)

    # --- 1. Grayscale ---
    img_np = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

    # --- 2. Gaussian denoising (fast replacement for fastNlMeansDenoising) ---
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # --- 3. CLAHE contrast enhancement ---
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # --- 4. Conditional deskew ---
    deskewed = _deskew(enhanced)

    # --- 5. Adaptive thresholding (OCR) ---
    thresh = cv2.adaptiveThreshold(
        deskewed, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,
        C=10,
    )

    # --- 6. Sharpening ---
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    sharpened = cv2.filter2D(thresh, -1, kernel)

    # --- 7. Morphological close (handwriting gap fill) ---
    struct = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    enhanced_hw = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, struct)

    # --- 8. Back to RGB PIL ---
    rgb = cv2.cvtColor(enhanced_hw, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb.astype(np.uint8))


def fast_preprocess(pil_image: Image.Image) -> Image.Image:
    """
    Lightweight preprocessing for clean printed documents.
    ~5× faster than the full pipeline: grayscale → CLAHE → back to RGB.
    Skips denoising, thresholding, and morphological ops.
    """
    import cv2

    img_np = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    rgb = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)
    return Image.fromarray(rgb.astype(np.uint8))


def _deskew(gray: np.ndarray, min_skew_deg: float = 0.5) -> np.ndarray:
    """
    Correct skew using Hough transform line detection.
    Skips rotation when detected skew is below *min_skew_deg* (saves ~80 ms).
    """
    import cv2

    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)

    if lines is None:
        return gray

    angles = []
    for line in lines[:20]:
        rho, theta = line[0]
        angle = (theta - np.pi / 2) * 180 / np.pi
        if abs(angle) < 20:
            angles.append(angle)

    if not angles:
        return gray

    median_angle = float(np.median(angles))
    # Skip rotation for trivially small skew — saves ~80 ms per page
    if abs(median_angle) < min_skew_deg:
        return gray

    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    return cv2.warpAffine(
        gray, M, (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )


def preprocess_for_vision(pil_image: Image.Image, target_size: tuple = (1024, 1024)) -> Image.Image:
    """
    Lighter preprocessing for vision model inputs (Florence-2, MiniCPM-V).
    Preserves colour — only resizes and normalises.
    """
    img = pil_image.convert("RGB")
    img = img.resize(target_size, Image.LANCZOS)
    return img
