"""
AIVENTRA — FastAPI Application Entry Point
"""
from __future__ import annotations

from contextlib import asynccontextmanager

import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.exceptions import AiventraError
from app.database import close_db, init_db

# Import all routers
from app.api.routes.health import router as health_router
from app.api.routes.upload import router as upload_router
from app.api.routes.analyze import router as analyze_router
from app.api.routes.ocr import router as ocr_router
from app.api.routes.extract import router as extract_router
from app.api.routes.reason import router as reason_router
from app.api.routes.rag import router as rag_router
from app.api.routes.cases import router as cases_router


# ------------------------------------------------------------------
# Application lifespan
# ------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialise DB pool and pre-load all AI models."""
    # Database
    await init_db()

    # Pre-load all AI models into the model registry
    from app.core.model_registry import ModelRegistry
    await ModelRegistry.initialize()

    # Pre-warm the autopsy knowledge base (loads PDF into memory cache)
    from app.knowledge.autopsy_kb import get_autopsy_manual_context
    kb_text = get_autopsy_manual_context()
    print(f"[KnowledgeBase] Autopsy manual loaded: {len(kb_text)} chars")

    yield

    # Shutdown: release DB pool
    await close_db()


# ------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------

app = FastAPI(
    title="AIVENTRA — Multimodal AI Forensic Intelligence System",
    description=(
        "Production-grade backend for forensic autopsy analysis using "
        "multimodal AI models, OCR, medical NLP, and hybrid RAG pipelines."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Global exception handler
# ------------------------------------------------------------------

@app.exception_handler(AiventraError)
async def aiventra_exception_handler(request: Request, exc: AiventraError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.__class__.__name__, "message": exc.message, "detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler — logs the full traceback and returns JSON 500."""
    tb = traceback.format_exc()
    print(f"[UNHANDLED ERROR] {request.method} {request.url}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": str(exc),
            "detail": tb.strip().splitlines()[-1] if tb.strip() else str(exc),
        },
    )


# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------

app.include_router(health_router,  tags=["System"])
app.include_router(upload_router,  prefix="/upload",     tags=["Ingestion"])
app.include_router(analyze_router, prefix="/analyze",    tags=["Analysis"])
app.include_router(ocr_router,     prefix="/ocr",        tags=["OCR"])
app.include_router(extract_router, prefix="/extract",    tags=["NLP"])
app.include_router(reason_router,  prefix="/reason",     tags=["Reasoning"])
app.include_router(rag_router,     prefix="/rag",        tags=["RAG"])
app.include_router(cases_router,   prefix="/case",       tags=["Cases"])


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        workers=settings.API_WORKERS,
        reload=False,
        timeout_keep_alive=300,   # 5-min keep-alive so browser doesn't drop
    )
