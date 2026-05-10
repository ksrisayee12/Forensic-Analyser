"""
AIVENTRA — Global Configuration
Reads all settings from environment variables / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    APP_NAME: str = "AIVENTRA"
    APP_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1
    MAX_UPLOAD_SIZE_MB: int = 100
    FAST_MODE: bool = True  # Disables heavy transformers for CPU users

    # ------------------------------------------------------------------
    # Supabase / PostgreSQL
    # ------------------------------------------------------------------
    SUPABASE_URL: str = "https://your-project-id.supabase.co"
    SUPABASE_KEY: str = "your-service-role-key"
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@db.your-project-id.supabase.co:5432/postgres"
    )

    # ------------------------------------------------------------------
    # Ollama
    # ------------------------------------------------------------------
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 300
    OLLAMA_MODELS: str = "llama3,qwen2.5,deepseek-r1,gemma2"

    @property
    def available_ollama_models(self) -> List[str]:
        return [m.strip() for m in self.OLLAMA_MODELS.split(",")]

    # ------------------------------------------------------------------
    # File Storage
    # ------------------------------------------------------------------
    UPLOAD_DIR: Path = Path("./uploads")
    FAISS_INDEX_DIR: Path = Path("./faiss_indices")
    MODEL_CACHE_DIR: Path = Path("./model_cache")

    # ------------------------------------------------------------------
    # GPU / Device
    # ------------------------------------------------------------------
    DEVICE: str = "cuda"
    CUDA_DEVICE_ID: int = 0

    # ------------------------------------------------------------------
    # OCR
    # ------------------------------------------------------------------
    PADDLEOCR_LANG: str = "en"
    PADDLEOCR_USE_GPU: bool = True
    TROCR_MODEL: str = "microsoft/trocr-large-handwritten"

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    LAYOUTLMV3_MODEL: str = "microsoft/layoutlmv3-base"

    # ------------------------------------------------------------------
    # Medical NLP
    # ------------------------------------------------------------------
    BIOBERT_MODEL: str = "dmis-lab/biobert-base-cased-v1.2"
    CLINICALBERT_MODEL: str = "medicalai/ClinicalBERT"
    SCISPACY_MODEL: str = "en_core_sci_lg"

    # ------------------------------------------------------------------
    # Vision Models
    # ------------------------------------------------------------------
    FLORENCE2_MODEL: str = "microsoft/Florence-2-large"
    MINICPM_MODEL: str = "openbmb/MiniCPM-V-2_6"

    # ------------------------------------------------------------------
    # Wound Detection
    # ------------------------------------------------------------------
    YOLO_MODEL_PATH: str = "./model_cache/yolov8x.pt"
    SAM2_CHECKPOINT: str = "./model_cache/sam2_hiera_large.pt"
    SAM2_CONFIG: str = "sam2_hiera_l.yaml"

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    BGE_MODEL: str = "BAAI/bge-large-en-v1.5"
    INSTRUCTOR_MODEL: str = "hkunlp/instructor-xl"
    EMBEDDING_DIMENSION: int = 1024

    # ------------------------------------------------------------------
    # RAG
    # ------------------------------------------------------------------
    RAG_TOP_K_SEMANTIC: int = 10
    RAG_TOP_K_BM25: int = 10
    RAG_TOP_K_RERANK: int = 5
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64

    def ensure_dirs(self) -> None:
        """Create all required local directories."""
        for d in (self.UPLOAD_DIR, self.FAISS_INDEX_DIR, self.MODEL_CACHE_DIR):
            Path(d).mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.ensure_dirs()
    return s


settings = get_settings()
