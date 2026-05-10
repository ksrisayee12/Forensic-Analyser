"""
AIVENTRA — Spatial Forensic Analysis Engine (Phase 8)
Correlates wound positions, trajectory arrows, body-map labels,
OCR findings, and image captions into a unified spatial understanding.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


def analyze_spatial(
    wound_detections: List[Dict[str, Any]],
    image_captions: List[Dict[str, Any]],
    text: str,
) -> Dict[str, Any]:
    """
    Perform spatial forensic analysis by correlating:
        - YOLO wound detections (with body locations)
        - Vision model captions (Florence-2 + MiniCPM-V)
        - OCR/NLP text for trajectory mentions

    Returns:
        {
            "wound_count": int,
            "body_zones": List[str],          # Distinct body zones affected
            "trajectory": str,               # Inferred trajectory description
            "entry_points": List[Dict],       # Entry wounds
            "exit_points": List[Dict],        # Exit wounds
            "retained_projectiles": bool,
            "mechanism": str,                # gsw / stab / blunt / unknown
            "severity_summary": str,
        }
    """
    all_detections: List[Dict] = []
    for wd in wound_detections:
        all_detections.extend(wd.get("detections", []))

    body_zones = list({d["body_location"] for d in all_detections if d.get("body_location")})
    entry_points = [d for d in all_detections if "entry" in d.get("class_name", "").lower()]
    exit_points = [d for d in all_detections if "exit" in d.get("class_name", "").lower()]

    # Trajectory inference from text
    trajectory = _infer_trajectory(text, image_captions)

    # Mechanism
    mechanism = _infer_mechanism(all_detections, text)

    # Retained projectile check
    retained = _check_retained_projectile(text)

    # Severity summary
    severity_counts = {"critical": 0, "severe": 0, "moderate": 0, "mild": 0, "unknown": 0}
    for d in all_detections:
        sev = d.get("severity", "unknown")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    severity_summary = (
        f"Critical: {severity_counts['critical']}, "
        f"Severe: {severity_counts['severe']}, "
        f"Moderate: {severity_counts['moderate']}, "
        f"Mild: {severity_counts['mild']}"
    )

    return {
        "wound_count": len(all_detections),
        "body_zones": body_zones,
        "trajectory": trajectory,
        "entry_points": entry_points,
        "exit_points": exit_points,
        "retained_projectiles": retained,
        "mechanism": mechanism,
        "severity_summary": severity_summary,
    }


def _infer_trajectory(text: str, captions: List[Dict]) -> str:
    """Extract trajectory description from text and image captions."""
    trajectory_patterns = [
        r"(right[\-\s]to[\-\s]left\s+trajectory)",
        r"(left[\-\s]to[\-\s]right\s+trajectory)",
        r"(front[\-\s]to[\-\s]back\s+trajectory)",
        r"(back[\-\s]to[\-\s]front\s+trajectory)",
        r"(downward\s+trajectory)",
        r"(upward\s+trajectory)",
        r"(lateral\s+trajectory)",
        r"(tangential\s+trajectory)",
        r"(perforating\s+wound)",
        r"(penetrating\s+wound)",
    ]

    all_text = text + " ".join(
        c.get("caption", "") + " " + c.get("wound_description", "")
        for c in captions
    )

    found: List[str] = []
    for pattern in trajectory_patterns:
        matches = re.findall(pattern, all_text, re.IGNORECASE)
        found.extend(matches)

    if found:
        return "; ".join(set(found))
    return "Trajectory not determinable from available evidence."


def _infer_mechanism(detections: List[Dict], text: str) -> str:
    """Infer primary wound mechanism."""
    class_names = [d.get("class_name", "").lower() for d in detections]

    if any("gunshot" in c or "gsw" in c for c in class_names):
        return "gunshot_wound"
    if any("stab" in c or "incised" in c for c in class_names):
        return "sharp_force_injury"
    if any("bruise" in c or "blunt" in c or "contusion" in c for c in class_names):
        return "blunt_force_trauma"

    # Text-based fallback
    text_lower = text.lower()
    if "gunshot" in text_lower or "bullet" in text_lower or "firearm" in text_lower:
        return "gunshot_wound"
    if "stab" in text_lower or "knife" in text_lower or "incised" in text_lower:
        return "sharp_force_injury"
    if "blunt" in text_lower or "contusion" in text_lower:
        return "blunt_force_trauma"
    if "burn" in text_lower or "thermal" in text_lower:
        return "thermal_injury"

    return "unknown"


def _check_retained_projectile(text: str) -> bool:
    """Check if text mentions a retained/recovered projectile."""
    patterns = [
        r"projectile\s+recover",
        r"bullet\s+recover",
        r"fragment\s+recover",
        r"retained\s+projectile",
        r"slug\s+recover",
        r"\bpr\b",  # abbreviation for projectile recovered
    ]
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in patterns)
