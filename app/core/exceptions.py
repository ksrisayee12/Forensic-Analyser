"""
AIVENTRA — Custom Exception Hierarchy
"""
from __future__ import annotations


class AiventraError(Exception):
    """Base exception for all AIVENTRA errors."""
    status_code: int = 500

    def __init__(self, message: str, detail: str | None = None) -> None:
        self.message = message
        self.detail = detail or message
        super().__init__(message)


# ------------------------------------------------------------------
# Ingestion
# ------------------------------------------------------------------
class IngestionError(AiventraError):
    """Raised when document ingestion fails."""
    status_code = 422


class UnsupportedFileTypeError(IngestionError):
    """Raised when an unsupported file format is provided."""
    status_code = 415


class FileTooLargeError(IngestionError):
    """Raised when the uploaded file exceeds the size limit."""
    status_code = 413


# ------------------------------------------------------------------
# OCR
# ------------------------------------------------------------------
class OCRError(AiventraError):
    """Raised when OCR processing fails."""
    status_code = 500


# ------------------------------------------------------------------
# Layout
# ------------------------------------------------------------------
class LayoutDetectionError(AiventraError):
    """Raised when layout detection fails."""
    status_code = 500


# ------------------------------------------------------------------
# NLP
# ------------------------------------------------------------------
class NLPError(AiventraError):
    """Raised when a medical NLP step fails."""
    status_code = 500


# ------------------------------------------------------------------
# Vision
# ------------------------------------------------------------------
class VisionError(AiventraError):
    """Raised when vision model inference fails."""
    status_code = 500


# ------------------------------------------------------------------
# Wound Detection
# ------------------------------------------------------------------
class WoundDetectionError(AiventraError):
    """Raised when wound / object detection fails."""
    status_code = 500


# ------------------------------------------------------------------
# Embedding
# ------------------------------------------------------------------
class EmbeddingError(AiventraError):
    """Raised when embedding generation fails."""
    status_code = 500


# ------------------------------------------------------------------
# Vector Store
# ------------------------------------------------------------------
class VectorStoreError(AiventraError):
    """Raised when FAISS index operations fail."""
    status_code = 500


# ------------------------------------------------------------------
# RAG
# ------------------------------------------------------------------
class RAGError(AiventraError):
    """Raised when RAG retrieval fails."""
    status_code = 500


# ------------------------------------------------------------------
# Reasoning
# ------------------------------------------------------------------
class OllamaConnectionError(AiventraError):
    """Raised when the Ollama server is unreachable."""
    status_code = 503


class ReasoningError(AiventraError):
    """Raised when forensic reasoning fails."""
    status_code = 500


# ------------------------------------------------------------------
# Database
# ------------------------------------------------------------------
class DatabaseError(AiventraError):
    """Raised when database operations fail."""
    status_code = 500


class CaseNotFoundError(DatabaseError):
    """Raised when a requested case does not exist."""
    status_code = 404
