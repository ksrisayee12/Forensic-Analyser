"""
AIVENTRA — Forensic Autopsy Knowledge Base
Loads the PEX02 Forensic Autopsy Manual as static reference context for LLM grounding.
"""
from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import List

# Path to the autopsy manual — bundled in the repo root
_MANUAL_PATH = Path(__file__).parent.parent.parent / "PEX02_Forensic Autopsy Manual.opt.pdf"

# Key sections to extract (first N chars of manual to stay within LLM context)
_MAX_MANUAL_CHARS = 12_000


@lru_cache(maxsize=1)
def get_autopsy_manual_context() -> str:
    """
    Extract and cache the text from the forensic autopsy reference manual.
    Returns a trimmed context string for use in LLM prompts.
    """
    if not _MANUAL_PATH.exists():
        return _FALLBACK_GUIDELINES

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(_MANUAL_PATH))
        pages_text: List[str] = []
        for page in doc:
            pages_text.append(page.get_text("text"))
        doc.close()

        full_text = "\n".join(pages_text).strip()
        # Return the most informative portion (beginning + middle for context)
        return full_text[:_MAX_MANUAL_CHARS]
    except Exception as e:
        print(f"[KnowledgeBase] Failed to load autopsy manual: {e}")
        return _FALLBACK_GUIDELINES


# Fallback if PDF is missing
_FALLBACK_GUIDELINES = """
FORENSIC AUTOPSY STANDARD GUIDELINES (Embedded Fallback):

1. EXTERNAL EXAMINATION: Document body habitus, decomposition state, identifying marks,
   clothing, injuries (abrasions, contusions, lacerations, incised wounds, gunshot wounds).

2. INTERNAL EXAMINATION: Document injuries to all major organ systems —
   CNS (brain/spinal cord), cardiovascular (heart/major vessels), respiratory (lungs),
   gastrointestinal, genitourinary, musculoskeletal.

3. WOUND DOCUMENTATION: For each wound, document: location (anatomical), size (cm),
   shape, margins, directionality, depth, associated findings (sooting, stippling, GSR).

4. TOXICOLOGY: Blood, urine, vitreous humor, bile sampling protocol.
   Common substances: ethanol, opioids, benzodiazepines, cannabinoids, cocaine metabolites.

5. CAUSE OF DEATH: Specific disease/injury → mechanism → manner (natural/accident/homicide/
   suicide/undetermined).

6. MANNER OF DEATH CRITERIA:
   - Homicide: Death caused by another person's volitional acts.
   - Suicide: Self-inflicted with intent to die.
   - Accident: Unintentional circumstances.
   - Natural: Disease process without external causative factors.
   - Undetermined: Insufficient evidence.
"""
