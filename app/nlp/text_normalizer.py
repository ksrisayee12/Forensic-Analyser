"""
AIVENTRA — Medical Text Normalizer (Phase 5 — Step 1)
Expands abbreviations, cleans OCR noise, normalizes medical terminology.
"""
from __future__ import annotations

import re
from typing import Dict

# Forensic/medical abbreviation expansion dictionary
MEDICAL_ABBREVIATIONS: Dict[str, str] = {
    # Anatomical
    "abd": "abdominal",
    "ant": "anterior",
    "post": "posterior",
    "lat": "lateral",
    "bilat": "bilateral",
    "ext": "external",
    "int": "internal",
    "sup": "superior",
    "inf": "inferior",
    "lt": "left",
    "rt": "right",
    "med": "medial",
    "prox": "proximal",
    "dist": "distal",
    "cerv": "cervical",
    "thorac": "thoracic",
    "lumb": "lumbar",
    # Injuries
    "lac": "laceration",
    "gsw": "gunshot wound",
    "gsws": "gunshot wounds",
    "swu": "stab wound upper",
    "cont": "contusion",
    "fx": "fracture",
    "hem": "hemorrhage",
    "hemo": "hemorrhage",
    "perf": "perforation",
    "pen": "penetrating",
    "blunt": "blunt force trauma",
    "ppe": "penetrating projectile entry",
    "ppx": "penetrating projectile exit",
    # Organs
    "ao": "aorta",
    "sma": "superior mesenteric artery",
    "ivc": "inferior vena cava",
    "ij": "internal jugular",
    "ca": "coronary artery",
    "lv": "left ventricle",
    "rv": "right ventricle",
    "la": "left atrium",
    "ra": "right atrium",
    # Forensic
    "mod": "manner of death",
    "cod": "cause of death",
    "tox": "toxicology",
    "bac": "blood alcohol concentration",
    "etoh": "ethanol",
    "pm": "postmortem",
    "tmi": "time of maximum injury",
    "bldg": "bleeding",
    "wt": "wound track",
    "pr": "projectile recovered",
    "pnr": "projectile not recovered",
    # Clinical
    "hx": "history",
    "dx": "diagnosis",
    "px": "prognosis",
    "c/o": "complains of",
    "s/p": "status post",
    "h/o": "history of",
    "w/": "with",
    "w/o": "without",
    "sig": "significant",
    "nkda": "no known drug allergies",
    "approx": "approximately",
    "bilat": "bilateral",
}


def normalize_text(text: str) -> str:
    """
    Clean and normalize raw OCR/forensic text.

    Steps:
        1. Remove non-printable characters
        2. Fix common OCR artifacts
        3. Expand medical abbreviations
        4. Normalize whitespace
        5. Normalize case for entities
    """
    if not text:
        return ""

    # 1. Remove non-printable characters
    text = re.sub(r"[^\x09\x0A\x0D\x20-\x7E]", " ", text)

    # 2. Fix common OCR artifacts
    text = re.sub(r"\|", "I", text)                          # pipe → I
    text = re.sub(r"0(?=[a-zA-Z])", "O", text)               # 0 → O before letters
    text = re.sub(r"(?<=[a-zA-Z])0", "o", text)              # 0 → o after letters
    text = re.sub(r"l(?=\d)", "1", text)                     # l → 1 before digits
    text = re.sub(r"(\w)\s*\-\s*(\w)", r"\1-\2", text)       # normalise hyphens

    # 3. Expand abbreviations (word-boundary aware, case-insensitive)
    for abbr, expansion in sorted(MEDICAL_ABBREVIATIONS.items(), key=lambda x: -len(x[0])):
        pattern = r"\b" + re.escape(abbr) + r"\b"
        text = re.sub(pattern, expansion, text, flags=re.IGNORECASE)

    # 4. Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return text
