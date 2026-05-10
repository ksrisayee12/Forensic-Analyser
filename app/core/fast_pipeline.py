"""
AIVENTRA — Lean Forensic Analysis Pipeline (Rewrite)

Design goals:
  - Complete in < 60s on any CPU
  - No heavy transformer models required
  - Grounded in the PEX02 Autopsy Manual knowledge base
  - Three clear phases:
      1. EXTRACT  — PyMuPDF text + PaddleOCR fallback
      2. ANALYSE  — SciSpaCy NER + regex forensic patterns
      3. REASON   — Ollama LLM structured report generation
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from app import database as db
from app.core.exceptions import IngestionError
from app.knowledge.autopsy_kb import get_autopsy_manual_context
from app.reasoning.ollama_client import ollama
from app.config import settings


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run_fast_pipeline(case_id: str, file_path: Path) -> Dict[str, Any]:
    """
    Execute the 3-phase lean forensic pipeline and persist results.
    Returns the complete forensic output dict.
    """
    await db.update_case_status(case_id, "processing")

    try:
        # ── Phase 1: Text extraction ─────────────────────────────────────
        raw_text = _extract_text(file_path)

        # ── Phase 2: Local forensic analysis (no GPU) ────────────────────
        entities     = _extract_entities(raw_text)
        mechanism    = _infer_mechanism(raw_text)
        trajectory   = _extract_trajectory(raw_text)
        tox_findings = _extract_toxicology_hits(raw_text)
        retained     = _check_retained_projectile(raw_text)

        spatial = {
            "wound_count": len([e for e in entities if e["entity_type"] == "INJURY"]),
            "body_zones": list({e["entity_value"] for e in entities if e["entity_type"] == "BODY_LOCATION"}),
            "trajectory": trajectory,
            "entry_points": [],
            "exit_points": [],
            "retained_projectiles": retained,
            "mechanism": mechanism,
            "severity_summary": _severity_summary(raw_text),
        }

        # ── Phase 3: LLM structured report ───────────────────────────────
        summary_result = await _generate_report(
            case_id=case_id,
            raw_text=raw_text,
            entities=entities,
            spatial=spatial,
            tox_findings=tox_findings,
        )

        # ── Persist ───────────────────────────────────────────────────────
        injuries = [
            {
                "wound_type": e["entity_value"],
                "body_location": "",
                "bbox": None,
                "confidence": e["confidence"],
                "severity": "",
            }
            for e in entities if e["entity_type"] == "INJURY"
        ]
        await db.insert_injuries(case_id, injuries)

        tox_records = [
            {"substance": t, "concentration": None, "unit": None, "notes": "text-extracted"}
            for t in tox_findings
        ]
        await db.insert_toxicology(case_id, tox_records)
        await db.insert_forensic_entities(case_id, entities)

        report = await db.insert_report(
            case_id,
            summary=summary_result["summary"],
            reasoning_model=settings.OLLAMA_DEFAULT_MODEL,
            raw_output=summary_result["raw_output"],
        )

        await db.update_case_status(case_id, "completed")

        result = {
            "case_id": case_id,
            "status": "completed",
            "entities": entities,
            "injuries": injuries,
            "spatial_analysis": spatial,
            "image_captions": [],
            "summary": summary_result["summary"],
            "report_id": str(report["id"]),
        }

        # ── Persist output.json to project root ──────────────────────────────
        _write_output_json(result)

        return result

    except Exception as exc:
        await db.update_case_status(case_id, "failed")
        raise IngestionError(f"Pipeline failed for case {case_id}: {exc}") from exc


# ---------------------------------------------------------------------------
# Phase 1 — Text Extraction
# ---------------------------------------------------------------------------

def _extract_text(file_path: Path) -> str:
    """
    Extract clean text from PDF or image using PyMuPDF first,
    falling back to PaddleOCR for image-only / scanned PDFs.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        text = _pymupdf_text(file_path)
        if len(text.strip()) > 100:
            return text
        # Scanned PDF — fall through to OCR
        return _paddle_ocr_pdf(file_path)

    # Image file
    return _paddle_ocr_image(file_path)


def _pymupdf_text(path: Path) -> str:
    import fitz
    doc = fitz.open(str(path))
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return "\n".join(pages)


def _paddle_ocr_pdf(path: Path) -> str:
    """Render each PDF page at 150 DPI (not 300!) and run PaddleOCR."""
    try:
        import fitz
        from app.ocr.paddle_ocr import run_paddleocr
        from PIL import Image

        doc = fitz.open(str(path))
        texts = []
        for page in doc:
            # 150 DPI is sufficient for OCR and 4x faster to render
            mat = fitz.Matrix(150 / 72, 150 / 72)
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            result = run_paddleocr(img)
            texts.append(result.get("text", ""))
        doc.close()
        return "\n".join(texts)
    except Exception as e:
        print(f"[Pipeline] PaddleOCR PDF fallback failed: {e}")
        return ""


def _paddle_ocr_image(path: Path) -> str:
    try:
        from app.ocr.paddle_ocr import run_paddleocr
        from PIL import Image
        img = Image.open(str(path)).convert("RGB")
        return run_paddleocr(img).get("text", "")
    except Exception as e:
        print(f"[Pipeline] PaddleOCR image failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# Phase 2 — Local Analysis (CPU-only, instant)
# ---------------------------------------------------------------------------

def _extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Combined entity extraction:
      a) SciSpaCy NER (if loaded)
      b) Regex patterns for forensic-specific terms not in SciSpaCy
    """
    entities: List[Dict[str, Any]] = []
    seen: set = set()

    def _add(etype: str, value: str, conf: float, source: str) -> None:
        key = (etype, value.lower().strip())
        if key not in seen and len(value.strip()) > 2:
            seen.add(key)
            entities.append({
                "entity_type": etype,
                "entity_value": value.strip(),
                "source": source,
                "confidence": round(conf, 3),
            })

    # --- SciSpaCy ---
    try:
        from app.core.model_registry import ModelRegistry
        from app.nlp.scispacy_engine import LABEL_MAP

        nlp = ModelRegistry.get("scispacy")
        if nlp:
            for start in range(0, min(len(text), 80_000), 8_000):
                chunk = text[start: start + 8_000]
                doc = nlp(chunk)
                for ent in doc.ents:
                    mapped = LABEL_MAP.get(ent.label_, ent.label_)
                    score = float(getattr(ent._, "score_doc", 0.75)) if hasattr(ent._, "score_doc") else 0.75
                    _add(mapped, ent.text, score, "scispacy")
    except Exception as e:
        print(f"[Pipeline] SciSpaCy extraction error: {e}")

    # --- Regex forensic patterns ---
    _PATTERNS = [
        ("INJURY",         r"\b(gunshot wound|gsw|stab wound|incised wound|laceration|contusion|abrasion|fracture|blunt force|perforation|penetrating wound)\b"),
        ("CAUSE_OF_DEATH",  r"\b(cause of death|manner of death|immediate cause|contributing cause)\s*[:\-]?\s*([^\n.]{5,80})"),
        ("MANNER_OF_DEATH", r"\b(homicide|suicide|accident|natural|undetermined)\b"),
        ("WEAPON",          r"\b(firearm|handgun|rifle|shotgun|knife|blunt object|ligature)\b"),
        ("BODY_LOCATION",   r"\b(head|neck|chest|thorax|abdomen|back|left|right|anterior|posterior|lateral|medial|torso|upper|lower)\b"),
        ("TOXIN",           r"\b(ethanol|alcohol|cocaine|heroin|fentanyl|morphine|methamphetamine|oxycodone|benzodiazepine|barbiturate|amphetamine|THC|cannabis)\b"),
        ("PROJECTILE",      r"\b(bullet|slug|pellet|fragment|projectile)\b"),
        ("TRAJECTORY",      r"\b(entrance wound|exit wound|wound track|tangential|perforating|penetrating)\b"),
    ]

    for etype, pattern in _PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            value = m.group(0).strip()
            _add(etype, value, 0.85, "regex")

    return entities


def _infer_mechanism(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["gunshot", "gsw", "firearm", "bullet", "rifle", "shotgun"]):
        return "gunshot_wound"
    if any(w in t for w in ["stab", "knife", "incised", "sharp force", "blade"]):
        return "sharp_force_injury"
    if any(w in t for w in ["blunt", "contusion", "club", "bat", "impact"]):
        return "blunt_force_trauma"
    if any(w in t for w in ["burn", "thermal", "fire", "scald"]):
        return "thermal_injury"
    if any(w in t for w in ["strangle", "asphyxia", "ligature", "hanging"]):
        return "asphyxia"
    return "undetermined"


def _extract_trajectory(text: str) -> str:
    patterns = [
        r"(right[\-\s]to[\-\s]left trajectory)",
        r"(left[\-\s]to[\-\s]right trajectory)",
        r"(front[\-\s]to[\-\s]back|back[\-\s]to[\-\s]front)",
        r"(downward trajectory|upward trajectory|lateral trajectory)",
        r"(perforating wound|penetrating wound)",
        r"(entrance.{0,40}exit)",
    ]
    found = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            found.append(m.group(0))
    return "; ".join(set(found)) if found else "Not determinable from available evidence."


def _extract_toxicology_hits(text: str) -> List[str]:
    pattern = r"\b(ethanol|alcohol|cocaine|heroin|fentanyl|morphine|methamphetamine|oxycodone|benzodiazepine|barbiturate|amphetamine|THC|cannabis|opioid|diazepam|lorazepam|alprazolam|acetaminophen|salicylate)\b"
    hits = set(m.group(0).lower() for m in re.finditer(pattern, text, re.IGNORECASE))
    return list(hits)


def _check_retained_projectile(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in ["projectile recover", "bullet recover", "retained projectile", "fragment recover"])


def _severity_summary(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["fatal", "death", "deceased", "killed", "lethal"]):
        return "Fatal"
    if any(w in t for w in ["critical", "severe", "life-threatening"]):
        return "Critical/Severe"
    if any(w in t for w in ["moderate", "significant"]):
        return "Moderate"
    return "Severity not explicitly stated"


# ---------------------------------------------------------------------------
# Phase 3 — LLM Report Generation
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are AIVENTRA, an expert forensic AI assistant specializing in medico-legal autopsy analysis.

RULES:
1. NEVER fabricate or hallucinate forensic evidence.
2. ONLY reason from the provided document text and extracted entities.
3. Cite specific text excerpts to support conclusions when possible.
4. Use precise forensic and medico-legal terminology.
5. If evidence is insufficient for a finding, state "Insufficient evidence."
6. Structure output with clear section headers.
"""


async def _generate_report(
    case_id: str,
    raw_text: str,
    entities: List[Dict[str, Any]],
    spatial: Dict[str, Any],
    tox_findings: List[str],
) -> Dict[str, Any]:
    """Send structured prompt to Ollama and return report."""

    autopsy_kb = get_autopsy_manual_context()

    # Format entities concisely
    entity_lines = "\n".join(
        f"  [{e['entity_type']}] {e['entity_value']} ({e['source']}, conf={e['confidence']:.2f})"
        for e in entities[:40]
    )

    # Limit raw text to what fits in context
    doc_excerpt = raw_text[:6000]

    prompt = f"""== FORENSIC AUTOPSY MANUAL REFERENCE GUIDELINES ==
{autopsy_kb[:3000]}

== DOCUMENT TEXT (extracted from uploaded report) ==
{doc_excerpt}

== EXTRACTED FORENSIC ENTITIES ==
{entity_lines if entity_lines else "None extracted."}

== FORENSIC ANALYSIS SUMMARY ==
Mechanism: {spatial['mechanism']}
Trajectory: {spatial['trajectory']}
Toxicology hits: {', '.join(tox_findings) if tox_findings else 'None detected'}
Retained projectile: {spatial['retained_projectiles']}
Severity: {spatial['severity_summary']}

== TASK ==
Based STRICTLY on the document text and entities above, generate a comprehensive forensic autopsy analysis report with the following sections:

1. CASE OVERVIEW
   - Document type, quality, and completeness

2. IDENTIFIED INJURIES
   - List each wound/injury with type, anatomical location, and characteristics

3. WOUND ANALYSIS
   - Mechanism of injury with supporting evidence
   - Entry/exit characteristics (if applicable)
   - Trajectory analysis (if applicable)

4. TOXICOLOGICAL FINDINGS
   - Substances identified and their forensic significance

5. CAUSE AND MANNER OF DEATH
   - Immediate cause of death
   - Mechanism (how it caused death)
   - Manner of death (homicide/suicide/accident/natural/undetermined)

6. FORENSIC CONCLUSIONS
   - Key findings and their investigative significance
   - Evidence gaps and limitations

Ground every conclusion in the document evidence. State clearly when evidence is insufficient.
"""

    raw_output = await ollama.generate(
        prompt=prompt,
        model=settings.OLLAMA_DEFAULT_MODEL,
        system=_SYSTEM_PROMPT,
        temperature=0.05,
        max_tokens=2500,
    )

    return {
        "summary": raw_output.strip(),
        "raw_output": raw_output,
        "model": settings.OLLAMA_DEFAULT_MODEL,
    }


# ---------------------------------------------------------------------------
# Output persistence helper
# ---------------------------------------------------------------------------

def _write_output_json(result: Dict[str, Any]) -> None:
    """
    Write the pipeline result to ``output.json`` in the project root.

    The file is overwritten on every successful run so the latest result is
    always available for inspection, debugging, or downstream consumers.
    A ``generated_at`` ISO-8601 timestamp is injected automatically.
    """
    output: Dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }

    # Project root = 2 levels above this file (app/core/fast_pipeline.py)
    output_path = Path(__file__).resolve().parent.parent.parent / "output.json"

    try:
        output_path.write_text(
            json.dumps(output, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        print(f"[Pipeline] output.json written → {output_path}")
    except Exception as e:
        # Non-fatal — never block the API response for a logging failure
        print(f"[Pipeline] Warning: could not write output.json: {e}")
