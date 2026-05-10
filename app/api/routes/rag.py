"""
AIVENTRA — POST /rag/query endpoint
Hybrid RAG query against a stored case.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGResult
from app.config import settings
from app.database import get_case
from app.embedding.bge_embedder import embed_query
from app.rag.context_builder import build_context
from app.rag.hybrid_retriever import hybrid_retrieve
from app.reasoning.forensic_reasoner import answer_forensic_query
from app.vectorstore.faiss_store import FAISSStore

router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse, summary="Query forensic case knowledge base")
async def rag_query(request: RAGQueryRequest):
    """
    Perform a hybrid RAG query against a case's stored forensic knowledge.

    Pipeline:
        1. Embed the query (BGE-large)
        2. FAISS semantic retrieval
        3. BM25 lexical retrieval
        4. RRF fusion + cross-encoder reranking
        5. Ollama LLM answer generation
    """
    # Verify case exists
    await get_case(request.case_id)

    store = FAISSStore(request.case_id)

    if store.count == 0:
        return RAGQueryResponse(
            case_id=request.case_id,
            query=request.query,
            answer="No embeddings found for this case. Run POST /analyze first.",
            model=request.model or settings.OLLAMA_DEFAULT_MODEL,
            retrieved_chunks=[],
            chunk_count=0,
        )

    # Retrieve (corpus reconstructed from the store's internal texts)
    corpus = store._texts
    retrieved = hybrid_retrieve(
        query=request.query,
        faiss_store=store,
        corpus=corpus,
        top_k_final=request.top_k,
    )

    context = build_context(retrieved, max_chars=6000)
    model = request.model or settings.OLLAMA_DEFAULT_MODEL

    answer_result = await answer_forensic_query(
        query=request.query,
        context=context,
        model=model,
    )

    return RAGQueryResponse(
        case_id=request.case_id,
        query=request.query,
        answer=answer_result["answer"],
        model=model,
        retrieved_chunks=[
            RAGResult(text=r["text"], score=r["score"], rank=r["rank"])
            for r in retrieved
        ],
        chunk_count=len(retrieved),
    )
