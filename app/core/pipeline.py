"""
AIVENTRA — Master Forensic Analysis Pipeline
Orchestrates all 13 processing phases for a given case.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from app import database as db
from app.config import settings
from app.core.exceptions import IngestionError
from app.ingestion.file_router import route_file
from app.preprocessing.image_processor import preprocess_image
from app.layout.layout_detector import detect_layout
from app.ocr.ocr_merger import run_ocr
from app.nlp.text_normalizer import normalize_text
from app.nlp.biobert_ner import extract_entities_biobert
from app.nlp.scispacy_engine import extract_entities_scispacy
from app.vision.florence_engine import caption_image
from app.vision.minicpm_engine import interpret_wound_image
from app.wound.yolo_detector import detect_wounds
from app.wound.sam2_segmentor import segment_wounds
from app.wound.spatial_analyzer import analyze_spatial
from app.embedding.bge_embedder import embed_chunks
from app.vectorstore.faiss_store import FAISSStore
from app.rag.hybrid_retriever import hybrid_retrieve
from app.rag.context_builder import build_context
from app.reasoning.forensic_reasoner import generate_forensic_summary
from app.utils.chunker import chunk_text


async def run_full_pipeline(case_id: str, file_path: Path) -> Dict[str, Any]:
    """
    Execute all 13 forensic analysis phases and persist results.

    Returns the assembled forensic output dict.
    """
    loop = asyncio.get_event_loop()

    await db.update_case_status(case_id, "processing")

    try:
        # ----------------------------------------------------------------
        # Phase 1 — Ingestion
        # ----------------------------------------------------------------
        ingestion_result = await loop.run_in_executor(None, route_file, file_path)
        raw_images: List[Any] = ingestion_result["images"]   # list of PIL Images
        raw_text: str = ingestion_result.get("text", "")

        # ----------------------------------------------------------------
        # Phase 2 — Preprocessing
        # ----------------------------------------------------------------
        preprocessed_images = await loop.run_in_executor(
            None, _preprocess_all, raw_images
        )

        # ----------------------------------------------------------------
        # Phase 3 — Layout Detection
        # ----------------------------------------------------------------
        layout_results = await loop.run_in_executor(
            None, _layout_all, preprocessed_images
        )

        # ----------------------------------------------------------------
        # Phase 4 — OCR + Handwriting Recognition
        # ----------------------------------------------------------------
        ocr_results = await loop.run_in_executor(
            None, _ocr_all, preprocessed_images, layout_results
        )
        ocr_text = "\n".join(r["text"] for r in ocr_results)
        combined_text = (raw_text + "\n" + ocr_text).strip()

        # ----------------------------------------------------------------
        # Phase 5 — Medical NLP
        # ----------------------------------------------------------------
        normalized_text = await loop.run_in_executor(
            None, normalize_text, combined_text
        )
        biobert_entities = await loop.run_in_executor(
            None, extract_entities_biobert, normalized_text
        )
        scispacy_entities = await loop.run_in_executor(
            None, extract_entities_scispacy, normalized_text
        )
        all_entities = _merge_entities(biobert_entities, scispacy_entities)

        # ----------------------------------------------------------------
        # Phase 6 — Image Understanding
        # ----------------------------------------------------------------
        image_captions: List[Dict[str, Any]] = []
        for i, img in enumerate(preprocessed_images):
            caption = await loop.run_in_executor(None, caption_image, img)
            wound_desc = await loop.run_in_executor(None, interpret_wound_image, img)
            image_captions.append({
                "index": i,
                "caption": caption,
                "wound_description": wound_desc,
            })

        # ----------------------------------------------------------------
        # Phase 7 — Wound Detection
        # ----------------------------------------------------------------
        wound_detections: List[Dict[str, Any]] = []
        for i, img in enumerate(preprocessed_images):
            detections = await loop.run_in_executor(None, detect_wounds, img)
            masks = await loop.run_in_executor(None, segment_wounds, img, detections)
            wound_detections.append({"image_index": i, "detections": detections, "masks": masks})

        # ----------------------------------------------------------------
        # Phase 8 — Spatial Forensic Analysis
        # ----------------------------------------------------------------
        spatial_analysis = await loop.run_in_executor(
            None, analyze_spatial, wound_detections, image_captions, normalized_text
        )

        # ----------------------------------------------------------------
        # Phase 9 — Entity Extraction (aggregated)
        # ----------------------------------------------------------------
        forensic_entities = _build_forensic_entities(
            all_entities, spatial_analysis, image_captions
        )

        # ----------------------------------------------------------------
        # Phase 10 — Embedding
        # ----------------------------------------------------------------
        chunks = chunk_text(normalized_text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
        caption_chunks = [cap["caption"] + " " + cap["wound_description"] for cap in image_captions]
        all_chunks = chunks + caption_chunks

        embedded = await loop.run_in_executor(None, embed_chunks, all_chunks)

        # ----------------------------------------------------------------
        # Phase 11 — FAISS Vector Storage
        # ----------------------------------------------------------------
        store = FAISSStore(case_id)
        await loop.run_in_executor(None, store.add, embedded)

        # ----------------------------------------------------------------
        # Phase 12 — Hybrid RAG (build forensic query)
        # ----------------------------------------------------------------
        forensic_query = _build_forensic_query(forensic_entities, normalized_text)
        retrieved = await loop.run_in_executor(
            None,
            hybrid_retrieve,
            forensic_query,
            store,
            all_chunks,
        )
        context = build_context(retrieved)

        # ----------------------------------------------------------------
        # Phase 13 — Forensic Reasoning
        # ----------------------------------------------------------------
        summary_result = await generate_forensic_summary(
            context=context,
            entities=forensic_entities,
            wound_detections=wound_detections,
            spatial_analysis=spatial_analysis,
            model=settings.OLLAMA_DEFAULT_MODEL,
        )

        # ----------------------------------------------------------------
        # Persist to database
        # ----------------------------------------------------------------
        injuries = _extract_injuries(wound_detections, forensic_entities)
        await db.insert_injuries(case_id, injuries)

        for cap in image_captions:
            await db.insert_image_finding(
                case_id,
                image_path=str(file_path),
                caption=cap["caption"],
                description=cap["wound_description"],
                model_used="florence2+minicpm",
            )

        tox_records = _extract_toxicology(forensic_entities)
        await db.insert_toxicology(case_id, tox_records)
        await db.insert_forensic_entities(case_id, forensic_entities)

        embedding_records = [
            {"text": e["text"], "embedding": e["embedding"], "model_used": "bge-large"}
            for e in embedded
        ]
        await db.insert_embeddings(case_id, embedding_records)

        report = await db.insert_report(
            case_id,
            summary=summary_result["summary"],
            reasoning_model=settings.OLLAMA_DEFAULT_MODEL,
            raw_output=summary_result["raw_output"],
        )

        await db.update_case_status(case_id, "completed")

        return {
            "case_id": case_id,
            "status": "completed",
            "entities": forensic_entities,
            "injuries": injuries,
            "spatial_analysis": spatial_analysis,
            "image_captions": image_captions,
            "summary": summary_result["summary"],
            "report_id": str(report["id"]),
        }

    except Exception as exc:
        await db.update_case_status(case_id, "failed")
        raise IngestionError(f"Pipeline failed for case {case_id}: {exc}") from exc


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _preprocess_all(images):
    return [preprocess_image(img) for img in images]


def _layout_all(images):
    return [detect_layout(img) for img in images]


def _ocr_all(images, layouts):
    return [run_ocr(img, layout) for img, layout in zip(images, layouts)]


def _merge_entities(biobert: List[Dict], scispacy: List[Dict]) -> List[Dict]:
    seen = set()
    merged = []
    for e in biobert + scispacy:
        key = (e.get("entity_type"), e.get("entity_value"))
        if key not in seen:
            seen.add(key)
            merged.append(e)
    return merged


def _build_forensic_entities(
    all_entities: List[Dict],
    spatial: Dict,
    captions: List[Dict],
) -> List[Dict]:
    entities = list(all_entities)
    for cap in captions:
        entities.append({
            "entity_type": "IMAGE_CAPTION",
            "entity_value": cap["caption"],
            "source": "florence2",
            "confidence": 0.9,
        })
        entities.append({
            "entity_type": "WOUND_DESCRIPTION",
            "entity_value": cap["wound_description"],
            "source": "minicpm",
            "confidence": 0.85,
        })
    if spatial.get("trajectory"):
        entities.append({
            "entity_type": "BALLISTIC_TRAJECTORY",
            "entity_value": spatial["trajectory"],
            "source": "spatial_analyzer",
            "confidence": 0.8,
        })
    return entities


def _extract_injuries(wound_detections: List[Dict], entities: List[Dict]) -> List[Dict]:
    injuries = []
    for wd in wound_detections:
        for det in wd.get("detections", []):
            injuries.append({
                "wound_type": det.get("class_name", "unknown"),
                "body_location": det.get("body_location", ""),
                "bbox": det.get("bbox"),
                "confidence": det.get("confidence", 0.0),
                "severity": det.get("severity", ""),
            })
    return injuries


def _extract_toxicology(entities: List[Dict]) -> List[Dict]:
    return [
        {
            "substance": e["entity_value"],
            "concentration": None,
            "unit": None,
            "notes": e.get("source", ""),
        }
        for e in entities
        if e.get("entity_type") in ("CHEMICAL", "DRUG", "TOXIN", "SUBSTANCE")
    ]


def _build_forensic_query(entities: List[Dict], text: str) -> str:
    key_terms = [
        e["entity_value"]
        for e in entities
        if e.get("entity_type") in (
            "INJURY", "WOUND", "ORGAN", "CAUSE_OF_DEATH", "MANNER_OF_DEATH",
            "WEAPON", "PROJECTILE", "TOXIN",
        )
    ][:10]
    query = "Forensic analysis: " + ", ".join(key_terms)
    if len(query) < 50 and text:
        query += " " + text[:200]
    return query
