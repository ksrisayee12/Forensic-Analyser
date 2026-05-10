"""
AIVENTRA — POST /reason endpoint
Run Ollama forensic reasoning on a processed case.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas.reasoning import ReasonRequest, ReasonResponse
from app.config import settings
from app.database import get_full_case, insert_report
from app.rag.context_builder import build_context, build_entity_context
from app.rag.hybrid_retriever import hybrid_retrieve
from app.reasoning.forensic_reasoner import generate_forensic_summary, multi_model_consensus
from app.vectorstore.faiss_store import FAISSStore
from app.embedding.bge_embedder import embed_query

router = APIRouter()


@router.post("", response_model=ReasonResponse, summary="Run forensic reasoning on a case")
async def reason_case(request: ReasonRequest):
    """
    Run Ollama-powered forensic reasoning on a previously analyzed case.

    Retrieves stored embeddings and entities from the database,
    performs hybrid RAG retrieval, and generates a new forensic summary.
    """
    case = await get_full_case(request.case_id)
    entities = case.get("forensic_entities", [])

    # Reconstruct corpus from stored embeddings
    embedding_records = case.get("embeddings", [])  # type: ignore
    # Note: embeddings are fetched separately if needed
    corpus = [e.get("chunk_text", "") for e in embedding_records]

    # Use FAISS store for retrieval
    store = FAISSStore(request.case_id)

    # Build query from entities
    key_terms = [e["entity_value"] for e in entities[:10]]
    query = "Forensic summary: " + ", ".join(key_terms) if key_terms else "Generate forensic autopsy summary"

    if store.count > 0:
        retrieved = hybrid_retrieve(query, store, corpus)
        context = build_context(retrieved)
    else:
        # Fallback: use stored report text or entity context
        prior_reports = case.get("reports", [])
        context = prior_reports[0].get("raw_output", "") if prior_reports else ""

    # Spatial analysis from injuries
    injuries = case.get("injuries", [])
    wound_detections = [{"detections": injuries}]
    from app.wound.spatial_analyzer import analyze_spatial

    image_findings = case.get("image_findings", [])
    captions = [{"caption": f.get("caption", ""), "wound_description": f.get("description", "")}
                for f in image_findings]
    spatial = analyze_spatial(wound_detections, captions, context)

    # Multi-model or single-model reasoning
    model = request.model or settings.OLLAMA_DEFAULT_MODEL

    if request.multi_model:
        multi_result = await multi_model_consensus(
            f"Provide a forensic autopsy summary based on:\n{context}\n\nEntities:\n{build_entity_context(entities)}"
        )
        summary = multi_result["responses"].get(model, "")
        multi_responses = multi_result["responses"]
    else:
        summary_result = await generate_forensic_summary(
            context=context,
            entities=entities,
            wound_detections=wound_detections,
            spatial_analysis=spatial,
            model=model,
        )
        summary = summary_result["summary"]
        multi_responses = None

    report = await insert_report(
        case_id=request.case_id,
        summary=summary,
        reasoning_model=model,
        raw_output=summary,
    )

    return ReasonResponse(
        case_id=request.case_id,
        summary=summary,
        model=model,
        report_id=str(report["id"]),
        multi_model_responses=multi_responses,
    )
