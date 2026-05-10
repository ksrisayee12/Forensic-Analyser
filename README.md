# AIVENTRA
## Multimodal AI Forensic Intelligence System

> **Production-grade backend** for forensic autopsy analysis using local multimodal AI, OCR, medical NLP, wound detection, and hybrid RAG pipelines. No cloud APIs. No LangChain.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [AI Architecture](#2-ai-architecture)
3. [Features](#3-features)
4. [Tech Stack](#4-tech-stack)
5. [Installation](#5-installation)
6. [Ollama Setup](#6-ollama-setup)
7. [Environment Configuration](#7-environment-configuration)
8. [Running the Server](#8-running-the-server)
9. [API Documentation](#9-api-documentation)
10. [Processing Pipeline](#10-processing-pipeline)
11. [Workflow Details](#11-workflow-details)
12. [Example API Requests & Responses](#12-example-api-requests--responses)
13. [GPU Requirements](#13-gpu-requirements)
14. [Performance Optimization](#14-performance-optimization)
15. [Future Roadmap](#15-future-roadmap)

---

## 1. Project Overview

AIVENTRA is a fully local, GPU-accelerated forensic AI backend that processes:

- Forensic autopsy reports (PDF, scanned)
- Handwritten doctor/pathologist notes
- Body injury diagrams and body maps
- Gunshot wound documentation sheets
- Crime-scene forensic images
- Toxicology reports
- Medico-legal PDFs
- Ballistic trajectory reports

The system extracts structured forensic intelligence, generates medico-legal summaries, and answers investigator queries — all grounded in extracted evidence with **zero hallucination tolerance**.

---

## 2. AI Architecture

```
INPUT (PDF / Image / TIFF)
         │
         ▼
┌─────────────────────────┐
│  Phase 1: Ingestion     │  PyMuPDF · pdfplumber · Pillow
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 2: Preprocessing │  OpenCV · scikit-image
│  CLAHE · Deskew · Sharp │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 3: Layout Detect │  LayoutLMv3 · Detectron2
│  Regions · Diagrams     │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 4: OCR Engine    │  PaddleOCR (printed)
│                         │  TrOCR (handwriting)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 5: Medical NLP   │  BioBERT · ClinicalBERT
│  Normalize · NER        │  SciSpacy
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 6: Vision Engine │  Florence-2 · MiniCPM-V
│  Caption · Interpret    │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 7: Wound Detect  │  YOLOv8 · SAM2
│  BBox · Mask · Severity │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 8: Spatial Anal. │  Trajectory · Mechanism
│  Entry/Exit · Zones     │  Retained Projectile
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 9: Entity Ext.   │  Merged: NLP + Vision
│  Injury · Tox · Ballistic│
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 10: Embeddings   │  BGE-large · Instructor-XL
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 11: FAISS Store  │  Per-case index · Cosine sim
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 12: Hybrid RAG   │  FAISS + BM25 + RRF
│  Cross-encoder Rerank   │  (No LangChain)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Phase 13: LLM Reason   │  Ollama: Llama3 / Qwen2.5
│  Forensic Summary       │  DeepSeek-R1 / Gemma2
└────────────┬────────────┘
             ▼
     FastAPI JSON Response
     Supabase PostgreSQL
```

---

## 3. Features

- **Multimodal ingestion** — PDF, JPG, PNG, TIFF, multi-page TIFF
- **Advanced OCR** — PaddleOCR for printed text + TrOCR for handwriting
- **Medical abbreviation expansion** — 60+ forensic/clinical abbreviations
- **Layout-aware processing** — detects body diagrams, handwritten regions, tables, trajectory arrows
- **Wound detection & segmentation** — YOLOv8 bounding boxes + SAM2 pixel masks
- **Body-map spatial analysis** — trajectory inference, entry/exit correlation, mechanism classification
- **Biomedical NER** — BioBERT + SciSpacy entity extraction with forensic type mapping
- **Vision understanding** — Florence-2 detailed captions + MiniCPM-V forensic wound interpretation
- **Hybrid RAG** — FAISS semantic + BM25 lexical + RRF fusion + cross-encoder reranking
- **Multi-model reasoning** — Llama3, Qwen2.5, DeepSeek-R1, Gemma2 via Ollama
- **Anti-hallucination enforcement** — strict evidence-grounded prompting
- **Supabase PostgreSQL persistence** — all cases, injuries, entities, reports stored
- **Per-case FAISS indices** — disk-persisted vector search per case

---

## 4. Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI 0.111 + Uvicorn |
| Schemas | Pydantic v2 |
| Database | Supabase PostgreSQL (asyncpg) |
| PDF Ingestion | PyMuPDF, pdfplumber |
| Image Processing | OpenCV, scikit-image, Pillow |
| Layout Analysis | LayoutLMv3 (HuggingFace) |
| OCR | PaddleOCR, TrOCR |
| Medical NLP | BioBERT, ClinicalBERT, SciSpacy |
| Vision | Florence-2-large, MiniCPM-V-2.6 |
| Wound Detection | YOLOv8 (Ultralytics), SAM2 |
| Embeddings | BGE-large-en-v1.5, Instructor-XL |
| Vector Store | FAISS (faiss-cpu / faiss-gpu) |
| RAG | Custom: FAISS + rank-bm25 + cross-encoder |
| LLM | Ollama (Llama3, Qwen2.5, DeepSeek-R1, Gemma2) |
| HTTP Client | httpx (async) |
| Retry | tenacity |

---

## 5. Installation

### Prerequisites
- Python 3.11+
- CUDA 12.1+ (recommended) or CPU fallback
- Ollama installed and running
- Supabase project (free tier works)

### Step 1 — Clone and set up environment

```bash
git clone https://github.com/yourorg/aiventra.git
cd aiventra
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### Step 2 — Install PyTorch with CUDA

```bash
# CUDA 12.1
pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cu121

# CPU only
pip install torch==2.3.0 torchvision==0.18.0
```

### Step 3 — Install core dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Install SciSpacy model

```bash
pip install https://s3-us-west-2.amazonaws.com/ai2-s3-scispacy/releases/v0.5.4/en_core_sci_lg-0.5.4.tar.gz
```

### Step 5 — Install Detectron2 (optional, for layout)

```bash
# CUDA 12.1 + PyTorch 2.3
pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu121/torch2.3/index.html
```

### Step 6 — Install SAM2 (optional, for wound segmentation)

```bash
pip install git+https://github.com/facebookresearch/segment-anything-2.git
```

### Step 7 — Download SAM2 checkpoint

```bash
mkdir -p model_cache
wget -P model_cache https://dl.fbaipublicfiles.com/segment_anything_2/072824/sam2_hiera_large.pt
```

---

## 6. Ollama Setup

### Install Ollama

```bash
# Windows / macOS
# Download from: https://ollama.com/download

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

### Start Ollama server

```bash
ollama serve
```

### Pull required models

```bash
# Primary reasoning model
ollama pull llama3

# Additional models
ollama pull qwen2.5
ollama pull deepseek-r1
ollama pull gemma2

# Verify
ollama list
```

---

## 7. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
DATABASE_URL=postgresql+asyncpg://postgres:password@db.your-project-id.supabase.co:5432/postgres

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3

# GPU
DEVICE=cuda
CUDA_DEVICE_ID=0
```

---

## 8. Running the Server

```bash
python -m app.main
```

Or with uvicorn directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

The API will be available at:
- `http://localhost:8000` — API root
- `http://localhost:8000/docs` — Swagger UI
- `http://localhost:8000/redoc` — ReDoc

> **Note**: On first startup, all AI models are pre-loaded into GPU/CPU memory. This may take 3–10 minutes depending on hardware.

---

## 9. API Documentation

### Endpoints Summary

| Method | Path | Description |
|---|---|---|
| `POST` | `/upload` | Upload a forensic document |
| `POST` | `/analyze` | Run full 13-phase pipeline |
| `POST` | `/ocr` | OCR only (no case created) |
| `POST` | `/extract` | Entity extraction from text |
| `POST` | `/reason` | Ollama reasoning on a case |
| `POST` | `/rag/query` | Hybrid RAG query |
| `GET` | `/case/{id}` | Retrieve full case record |
| `GET` | `/health` | System health check |

---

## 10. Processing Pipeline

### Phase 1 — Ingestion
- PDF: PyMuPDF extracts text + renders each page at 300 DPI; pdfplumber extracts tables
- Images: Pillow loads JPG/PNG/TIFF; multi-page TIFFs are split into frames

### Phase 2 — Preprocessing (OpenCV)
1. Grayscale conversion
2. Non-local means denoising
3. CLAHE contrast enhancement
4. Hough-transform deskewing
5. Adaptive Gaussian thresholding
6. Sharpening kernel
7. Morphological closing (handwriting enhancement)

### Phase 3 — Layout Detection (LayoutLMv3)
Detects: text, titles, tables, figures, handwritten notes, body diagrams, wound annotations, trajectory arrows, signatures, labels

### Phase 4 — OCR
- **PaddleOCR**: Full-page printed text with per-block bounding boxes
- **TrOCR**: Targeted on handwriting regions identified by layout detection
- **Merger**: Confidence-weighted fusion; TrOCR applied only to handwritten regions

### Phase 5 — Medical NLP
- **Text Normalizer**: 60+ medical/forensic abbreviation expansions + OCR artifact correction
- **BioBERT NER**: Biomedical entity recognition with forensic label mapping
- **ClinicalBERT**: MLM-based correction of garbled medical tokens
- **SciSpacy**: Scientific NER + noun phrase extraction

### Phase 6 — Vision Understanding
- **Florence-2**: Detailed image captioning using `<DETAILED_CAPTION>` task token
- **MiniCPM-V**: Wound/trauma interpretation using forensic pathologist system prompt

### Phase 7 — Wound Detection
- **YOLOv8**: Detects wound classes with bounding boxes and confidence
- **SAM2**: Generates pixel-level segmentation masks per detection
- Body location inferred from Y-position of bounding box relative to image height

### Phase 8 — Spatial Analysis
- Trajectory extraction via regex patterns (right-to-left, front-to-back, upward, etc.)
- Mechanism classification: GSW / sharp-force / blunt-force / thermal
- Retained projectile detection from text keywords
- Severity aggregation across all detections

### Phase 9 — Entity Extraction
All entities merged from: BioBERT + SciSpacy + Florence-2 captions + MiniCPM-V descriptions + spatial analysis

### Phase 10 — Embeddings
- **BGE-large**: 1024-dim normalized vectors with retrieval prefix
- **Instructor-XL**: Task-specific embeddings (injury, toxicology, trajectory, general)

### Phase 11 — FAISS Vector Store
- Per-case `IndexFlatIP` with L2-normalized vectors (= cosine similarity)
- Persisted to `./faiss_indices/{case_id}.index` + `.texts.npy`

### Phase 12 — Hybrid RAG
1. BGE-large query embedding → FAISS search (top-10)
2. BM25 tokenized search (top-10)
3. Reciprocal Rank Fusion (RRF, k=60)
4. Cross-encoder reranking (`ms-marco-MiniLM-L-6-v2`)
5. Context window assembly with evidence numbering

### Phase 13 — Forensic Reasoning (Ollama)
- System prompt enforces: no hallucination, evidence-grounded only, clinical language
- Structured output: Case Overview → Injuries → Wound Analysis → Toxicology → COD/MOD → Conclusions
- Multi-model consensus mode available via `/reason` with `multi_model: true`

---

## 11. Workflow Details

### OCR Workflow
```
Image Input
    → Grayscale + CLAHE + Deskew + Threshold
    → Layout Detection (LayoutLMv3)
    → PaddleOCR (full page, printed text)
    → [If handwriting regions detected] TrOCR on cropped regions
    → Merge by confidence
    → Text normalization (abbreviation expansion)
```

### Vision Workflow
```
PIL Image
    → Preprocess for vision (resize to 1024x1024, RGB)
    → Florence-2: <DETAILED_CAPTION> → forensic image description
    → MiniCPM-V: forensic pathologist prompt → wound interpretation
    → Outputs stored as image_findings in DB
```

### RAG Workflow
```
Query string
    → BGE-large embedding
    → FAISS: top-10 semantic results
    → BM25: top-10 keyword results
    → RRF fusion → ranked merged list
    → Cross-encoder rerank → top-5
    → Context assembly (max 8000 chars, evidence numbered)
    → Ollama prompt with context → grounded answer
```

### Medical NLP Workflow
```
Raw OCR text
    → normalize_text() (regex + abbreviation expansion)
    → BioBERT NER pipeline (chunked, 400 words/chunk)
    → SciSpacy NER (windowed, 10k chars/window)
    → ClinicalBERT MLM correction (suspicious tokens)
    → Entity deduplication
    → Forensic type mapping
```

---

## 12. Example API Requests & Responses

### POST /upload
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@autopsy_report.pdf"
```
```json
{
  "case_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "autopsy_report.pdf",
  "file_type": "pdf",
  "status": "pending",
  "message": "File uploaded successfully. Use POST /analyze to process this case.",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### POST /analyze
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"case_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "model": "llama3"}'
```
```json
{
  "case_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "completed",
  "entities": [
    {"entity_type": "INJURY", "entity_value": "gunshot wound", "source": "biobert", "confidence": 0.97},
    {"entity_type": "ORGAN", "entity_value": "left ventricle", "source": "scispacy", "confidence": 0.91},
    {"entity_type": "CAUSE_OF_DEATH", "entity_value": "hemorrhage", "source": "biobert", "confidence": 0.89}
  ],
  "injuries": [
    {"wound_type": "gunshot_entry", "body_location": "chest/upper torso", "confidence": 0.94, "severity": "critical"}
  ],
  "spatial_analysis": {
    "wound_count": 2,
    "body_zones": ["chest/upper torso", "abdomen"],
    "trajectory": "right-to-left trajectory",
    "mechanism": "gunshot_wound",
    "retained_projectiles": true,
    "severity_summary": "Critical: 1, Severe: 1, Moderate: 0, Mild: 0"
  },
  "summary": "## FORENSIC AUTOPSY SUMMARY\n\n### 1. CASE OVERVIEW\nA single PDF autopsy report was analyzed...",
  "report_id": "7b3e1234-ab12-4f56-c789-de0123456789"
}
```

### POST /ocr
```bash
curl -X POST http://localhost:8000/ocr \
  -F "file=@handwritten_notes.jpg"
```
```json
{
  "text": "GSW entry wound left anterior chest wall 4th ICS\nProjectile recovered from posterior thoracic cavity",
  "blocks": [
    {"text": "GSW entry wound left anterior chest wall 4th ICS", "confidence": 0.91, "source": "trocr"},
    {"text": "Projectile recovered from posterior thoracic cavity", "confidence": 0.88, "source": "paddleocr"}
  ],
  "confidence": 0.895,
  "page_count": 1
}
```

### POST /extract
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "abd lac with hem to the ao. GSW entry 4th ICS lat.", "use_llm": false}'
```
```json
{
  "entities": [
    {"entity_type": "INJURY", "entity_value": "abdominal laceration", "source": "biobert", "confidence": 0.93},
    {"entity_type": "INJURY", "entity_value": "hemorrhage", "source": "scispacy", "confidence": 0.89},
    {"entity_type": "ORGAN", "entity_value": "aorta", "source": "biobert", "confidence": 0.87}
  ],
  "entity_count": 3,
  "sources_used": ["biobert", "scispacy"]
}
```

### POST /rag/query
```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"case_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "query": "What was the ballistic trajectory?", "top_k": 5}'
```
```json
{
  "case_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "query": "What was the ballistic trajectory?",
  "answer": "Based on the forensic evidence, the ballistic trajectory was determined to be right-to-left, with the projectile entering the left anterior chest wall at the 4th intercostal space and traveling posteriorly. The retained projectile was recovered from the posterior thoracic cavity.",
  "model": "llama3",
  "retrieved_chunks": [
    {"text": "GSW entry wound left anterior chest wall 4th ICS...", "score": 0.921, "rank": 1}
  ],
  "chunk_count": 3
}
```

### GET /case/{id}
```bash
curl http://localhost:8000/case/3fa85f64-5717-4562-b3fc-2c963f66afa6
```

### GET /health
```bash
curl http://localhost:8000/health
```
```json
{
  "status": "ok",
  "device": "cuda",
  "gpu_memory": {"device": "NVIDIA RTX 4090", "allocated_gb": 18.4, "reserved_gb": 22.1, "total_gb": 24.0},
  "models_loaded": {
    "paddleocr": true, "trocr_model": true, "layoutlmv3_model": true,
    "biobert_model": true, "clinicalbert_model": true, "scispacy": true,
    "florence2_model": true, "minicpm_model": true, "yolo": true,
    "sam2": true, "bge": true, "instructor": true
  },
  "ollama_available": true,
  "ollama_models": ["llama3:latest", "qwen2.5:latest", "deepseek-r1:latest", "gemma2:latest"]
}
```

---

## 13. GPU Requirements

| Configuration | Minimum | Recommended | Optimal |
|---|---|---|---|
| VRAM | 16 GB | 24 GB | 48 GB |
| GPU | RTX 3090 | RTX 4090 | A100/H100 |
| RAM | 32 GB | 64 GB | 128 GB |
| Storage | 100 GB | 250 GB | 500 GB |

### VRAM Breakdown (approximate)

| Model | VRAM |
|---|---|
| Florence-2-large (fp16) | ~4.5 GB |
| MiniCPM-V-2.6 (fp16) | ~8.5 GB |
| TrOCR-large | ~1.5 GB |
| LayoutLMv3-base | ~0.5 GB |
| BioBERT | ~0.4 GB |
| ClinicalBERT | ~0.4 GB |
| YOLOv8x | ~0.6 GB |
| SAM2-large | ~2.5 GB |
| BGE-large | ~1.2 GB |
| Instructor-XL | ~5.0 GB |
| **Total** | **~25 GB** |

> Ollama LLMs run in their own process with separate VRAM allocation (4-bit quantized Llama3 ≈ 4.5 GB).

### CPU Fallback
All models support CPU inference. Set `DEVICE=cpu` in `.env`. Expect 10–50x slower processing.

---

## 14. Performance Optimization

### Model Loading
- All models loaded once at startup via `ModelRegistry` — zero per-request cold starts
- Concurrent loading using `asyncio.gather` with executor threads

### Inference
- All blocking inference dispatched to thread pool via `asyncio.get_event_loop().run_in_executor()`
- FastAPI stays non-blocking throughout

### OCR
- TrOCR only applied to handwriting regions (not full page) — saves 60-80% of TrOCR calls
- PaddleOCR runs on GPU with `use_gpu=True`

### Embeddings
- BGE-large: batched encoding with `batch_size=32`
- Instructor-XL: batched with `batch_size=16`

### FAISS
- `IndexFlatIP` with L2-normalized vectors gives exact cosine similarity
- Upgrade to `IndexIVFFlat` with `nlist=100` for 100k+ chunks per case

### Ollama
- `temperature=0.05` for forensic summaries (deterministic, factual)
- `num_predict=2048–3000` — sufficient for forensic reports

### Recommended Production Settings
```env
DEVICE=cuda
PADDLEOCR_USE_GPU=true
RAG_TOP_K_SEMANTIC=10
RAG_TOP_K_BM25=10
RAG_TOP_K_RERANK=5
CHUNK_SIZE=512
CHUNK_OVERLAP=64
```

---

## 15. Future Roadmap

### Near-term
- [ ] Streaming forensic summaries via Server-Sent Events
- [ ] Batch case processing pipeline
- [ ] Custom YOLOv8 model fine-tuned on forensic wound datasets
- [ ] DICOM medical image support
- [ ] Toxicology structured report parser (HL7 FHIR)

### Mid-term
- [ ] Timeline reconstruction from multi-case analysis
- [ ] Comparative wound analysis across cases
- [ ] Ballistic trajectory 3D visualization data output
- [ ] Custom BioBERT fine-tuning on autopsy corpora
- [ ] pgvector integration for Supabase native vector search

### Long-term
- [ ] Multi-case forensic intelligence graph (Neo4j)
- [ ] Expert system rule engine for cause-of-death classification
- [ ] Federated forensic knowledge base across agencies
- [ ] Automated chain-of-custody documentation generation
- [ ] Integration with NCIC and forensic database APIs

---

## License

MIT License — For research and legitimate forensic investigation use only.

> **Disclaimer**: AIVENTRA is an AI-assisted forensic analysis tool. All outputs must be reviewed and validated by qualified forensic pathologists and medico-legal professionals. AI-generated analysis is supplementary and does not replace expert human judgment.
