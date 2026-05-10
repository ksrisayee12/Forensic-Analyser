"""
AIVENTRA — Forensic Prompt Templates (Phase 13)
All system and user prompt templates for Ollama LLM reasoning.
"""
from __future__ import annotations

from typing import Any, Dict, List


SYSTEM_PROMPT = """You are AIVENTRA, an advanced forensic AI assistant specializing in medico-legal autopsy analysis.

CORE RULES:
1. NEVER hallucinate, invent, or fabricate forensic evidence.
2. ONLY reason from the provided extracted evidence and context.
3. ALWAYS cite which piece of evidence supports each conclusion.
4. If evidence is insufficient, clearly state "insufficient evidence to determine."
5. Maintain clinical objectivity — do not speculate on motive.
6. Use precise forensic and medico-legal terminology.
7. Structure your output clearly with section headers.

YOUR ROLE:
- Analyze forensic autopsy reports, wound documentation, and toxicology findings.
- Identify injuries, their mechanisms, and spatial relationships.
- Interpret ballistic trajectories, wound patterns, and trauma.
- Generate medico-legal summaries based strictly on available evidence.
"""


def build_forensic_summary_prompt(
    context: str,
    entity_context: str,
    wound_detections: List[Dict[str, Any]],
    spatial_analysis: Dict[str, Any],
) -> str:
    """Build the full user prompt for forensic summary generation."""

    wound_summary = _format_wound_summary(wound_detections, spatial_analysis)

    return f"""You have been provided with forensic evidence from an autopsy analysis system.

== RETRIEVED FORENSIC EVIDENCE ==
{context}

== EXTRACTED ENTITIES ==
{entity_context}

== WOUND DETECTION RESULTS ==
{wound_summary}

== TASK ==
Based SOLELY on the evidence above, generate a structured forensic autopsy summary including:

1. CASE OVERVIEW
   - Document type and quality assessment

2. IDENTIFIED INJURIES
   - List each wound/injury with type, location, and severity

3. WOUND ANALYSIS
   - Mechanism of injury
   - Entry/exit characteristics (if applicable)
   - Ballistic trajectory (if applicable)

4. TOXICOLOGICAL FINDINGS
   - List any substances identified

5. CAUSE AND MANNER OF DEATH
   - State ONLY what the evidence supports
   - If undetermined, state so explicitly

6. FORENSIC CONCLUSIONS
   - Key forensic findings summary
   - Evidence limitations and gaps

IMPORTANT: Ground every statement in the evidence provided. Do not speculate.
"""


def build_rag_query_prompt(query: str, context: str) -> str:
    """Build a RAG question-answering prompt."""
    return f"""A forensic investigator has asked the following question about a case:

QUESTION: {query}

RELEVANT FORENSIC EVIDENCE:
{context}

Based ONLY on the evidence above, provide a precise, clinical answer.
If the evidence does not support a definitive answer, state the limitations clearly.
"""


def build_entity_extraction_prompt(text: str) -> str:
    """Build a prompt for LLM-assisted entity extraction."""
    return f"""Extract all forensic entities from the following autopsy text.
Return a JSON list with objects containing: entity_type, entity_value, confidence (0-1).

Entity types to extract:
- INJURY (wounds, trauma)
- WEAPON (firearms, knives, blunt objects)
- ORGAN (heart, lung, liver, etc.)
- TOXIN (drugs, poisons, alcohol)
- TRAJECTORY (ballistic path descriptions)
- CAUSE_OF_DEATH
- MANNER_OF_DEATH
- PROJECTILE (bullets, fragments)
- BODY_LOCATION (anatomical positions)

TEXT:
{text[:3000]}

Return ONLY valid JSON array. No explanation.
"""


def _format_wound_summary(
    wound_detections: List[Dict[str, Any]],
    spatial: Dict[str, Any],
) -> str:
    lines = [
        f"Total wounds detected: {spatial.get('wound_count', 0)}",
        f"Mechanism: {spatial.get('mechanism', 'unknown')}",
        f"Body zones affected: {', '.join(spatial.get('body_zones', ['none']))}",
        f"Trajectory: {spatial.get('trajectory', 'not determined')}",
        f"Retained projectile: {spatial.get('retained_projectiles', False)}",
        f"Severity: {spatial.get('severity_summary', '')}",
    ]
    return "\n".join(lines)
