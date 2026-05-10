"""
AIVENTRA — Model Registry Singleton
Loads and holds all AI models once at startup, reused across requests.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from app.config import settings
from app.utils.gpu_utils import get_device


class ModelRegistry:
    """
    Singleton that pre-loads all AI models into memory at startup.
    All pipeline modules retrieve model instances from here.
    """

    _models: Dict[str, Any] = {}
    _initialised: bool = False

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------

    @classmethod
    async def initialize(cls) -> None:
        if cls._initialised:
            return

        loop = asyncio.get_event_loop()

        # Load models concurrently via executor (they block GIL)
        await asyncio.gather(
            loop.run_in_executor(None, cls._load_paddleocr),
            loop.run_in_executor(None, cls._load_trocr),
            loop.run_in_executor(None, cls._load_layoutlmv3),
            loop.run_in_executor(None, cls._load_biobert),
            loop.run_in_executor(None, cls._load_clinicalbert),
            loop.run_in_executor(None, cls._load_scispacy),
            loop.run_in_executor(None, cls._load_florence2),
            loop.run_in_executor(None, cls._load_minicpm),
            loop.run_in_executor(None, cls._load_yolo),
            loop.run_in_executor(None, cls._load_sam2),
            loop.run_in_executor(None, cls._load_bge),
            loop.run_in_executor(None, cls._load_instructor),
        )

        cls._initialised = True

    # ------------------------------------------------------------------
    # Individual loaders
    # ------------------------------------------------------------------

    @classmethod
    def _load_paddleocr(cls) -> None:
        try:
            from paddleocr import PaddleOCR
            use_gpu = settings.PADDLEOCR_USE_GPU and get_device() == "cuda"
            cls._models["paddleocr"] = PaddleOCR(
                use_angle_cls=True,
                lang=settings.PADDLEOCR_LANG,
                use_gpu=use_gpu,
                show_log=False,
            )
        except Exception as e:
            cls._models["paddleocr"] = None
            print(f"[ModelRegistry] PaddleOCR load failed: {e}")

    @classmethod
    def _load_trocr(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["trocr_processor"] = None
            cls._models["trocr_model"] = None
            return
        try:
            import torch
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel

            device = get_device()
            processor = TrOCRProcessor.from_pretrained(settings.TROCR_MODEL)
            model = VisionEncoderDecoderModel.from_pretrained(settings.TROCR_MODEL)
            model.to(device)
            model.eval()
            cls._models["trocr_processor"] = processor
            cls._models["trocr_model"] = model
        except Exception as e:
            cls._models["trocr_processor"] = None
            cls._models["trocr_model"] = None
            print(f"[ModelRegistry] TrOCR load failed: {e}")

    @classmethod
    def _load_layoutlmv3(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["layoutlmv3_extractor"] = None
            cls._models["layoutlmv3_model"] = None
            return
        try:
            from transformers import LayoutLMv3FeatureExtractor, LayoutLMv3ForTokenClassification

            device = get_device()
            extractor = LayoutLMv3FeatureExtractor.from_pretrained(settings.LAYOUTLMV3_MODEL)
            model = LayoutLMv3ForTokenClassification.from_pretrained(settings.LAYOUTLMV3_MODEL)
            model.to(device)
            model.eval()
            cls._models["layoutlmv3_extractor"] = extractor
            cls._models["layoutlmv3_model"] = model
        except Exception as e:
            cls._models["layoutlmv3_extractor"] = None
            cls._models["layoutlmv3_model"] = None
            print(f"[ModelRegistry] LayoutLMv3 load failed: {e}")

    @classmethod
    def _load_biobert(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["biobert_tokenizer"] = None
            cls._models["biobert_model"] = None
            return
        try:
            from transformers import AutoModelForTokenClassification, AutoTokenizer

            device = get_device()
            tokenizer = AutoTokenizer.from_pretrained(settings.BIOBERT_MODEL)
            model = AutoModelForTokenClassification.from_pretrained(settings.BIOBERT_MODEL)
            model.to(device)
            model.eval()
            cls._models["biobert_tokenizer"] = tokenizer
            cls._models["biobert_model"] = model
        except Exception as e:
            cls._models["biobert_tokenizer"] = None
            cls._models["biobert_model"] = None
            print(f"[ModelRegistry] BioBERT load failed: {e}")

    @classmethod
    def _load_clinicalbert(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["clinicalbert_tokenizer"] = None
            cls._models["clinicalbert_model"] = None
            return
        try:
            from transformers import AutoModelForMaskedLM, AutoTokenizer

            device = get_device()
            tokenizer = AutoTokenizer.from_pretrained(settings.CLINICALBERT_MODEL)
            model = AutoModelForMaskedLM.from_pretrained(settings.CLINICALBERT_MODEL)
            model.to(device)
            model.eval()
            cls._models["clinicalbert_tokenizer"] = tokenizer
            cls._models["clinicalbert_model"] = model
        except Exception as e:
            cls._models["clinicalbert_tokenizer"] = None
            cls._models["clinicalbert_model"] = None
            print(f"[ModelRegistry] ClinicalBERT load failed: {e}")

    @classmethod
    def _load_scispacy(cls) -> None:
        try:
            import spacy

            nlp = spacy.load(settings.SCISPACY_MODEL)
            cls._models["scispacy"] = nlp
        except Exception as e:
            cls._models["scispacy"] = None
            print(f"[ModelRegistry] SciSpacy load failed: {e}")

    @classmethod
    def _load_florence2(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["florence2_processor"] = None
            cls._models["florence2_model"] = None
            return
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoProcessor

            device = get_device()
            processor = AutoProcessor.from_pretrained(
                settings.FLORENCE2_MODEL, trust_remote_code=True
            )
            model = AutoModelForCausalLM.from_pretrained(
                settings.FLORENCE2_MODEL,
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            )
            model.to(device)
            model.eval()
            cls._models["florence2_processor"] = processor
            cls._models["florence2_model"] = model
        except Exception as e:
            cls._models["florence2_processor"] = None
            cls._models["florence2_model"] = None
            print(f"[ModelRegistry] Florence-2 load failed: {e}")

    @classmethod
    def _load_minicpm(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["minicpm_tokenizer"] = None
            cls._models["minicpm_model"] = None
            return
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer

            device = get_device()
            tokenizer = AutoTokenizer.from_pretrained(
                settings.MINICPM_MODEL, trust_remote_code=True
            )
            model = AutoModel.from_pretrained(
                settings.MINICPM_MODEL,
                trust_remote_code=True,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            )
            model.to(device)
            model.eval()
            cls._models["minicpm_tokenizer"] = tokenizer
            cls._models["minicpm_model"] = model
        except Exception as e:
            cls._models["minicpm_tokenizer"] = None
            cls._models["minicpm_model"] = None
            print(f"[ModelRegistry] MiniCPM-V load failed: {e}")

    @classmethod
    def _load_yolo(cls) -> None:
        try:
            from ultralytics import YOLO

            model = YOLO(settings.YOLO_MODEL_PATH)
            cls._models["yolo"] = model
        except Exception as e:
            cls._models["yolo"] = None
            print(f"[ModelRegistry] YOLOv8 load failed: {e}")

    @classmethod
    def _load_sam2(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["sam2"] = None
            return
        try:
            import torch
            from sam2.build_sam import build_sam2
            from sam2.sam2_image_predictor import SAM2ImagePredictor

            device = get_device()
            sam2_model = build_sam2(
                settings.SAM2_CONFIG,
                settings.SAM2_CHECKPOINT,
                device=device,
            )
            predictor = SAM2ImagePredictor(sam2_model)
            cls._models["sam2"] = predictor
        except Exception as e:
            cls._models["sam2"] = None
            print(f"[ModelRegistry] SAM2 load failed: {e}")

    @classmethod
    def _load_bge(cls) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(settings.BGE_MODEL)
            cls._models["bge"] = model
        except Exception as e:
            cls._models["bge"] = None
            print(f"[ModelRegistry] BGE-large load failed: {e}")

    @classmethod
    def _load_instructor(cls) -> None:
        if getattr(settings, "FAST_MODE", False):
            cls._models["instructor"] = None
            return
        try:
            from InstructorEmbedding import INSTRUCTOR

            model = INSTRUCTOR(settings.INSTRUCTOR_MODEL)
            cls._models["instructor"] = model
        except Exception as e:
            cls._models["instructor"] = None
            print(f"[ModelRegistry] Instructor-XL load failed: {e}")

    # ------------------------------------------------------------------
    # Accessor
    # ------------------------------------------------------------------

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        return cls._models.get(key)

    @classmethod
    def status(cls) -> Dict[str, bool]:
        """Return a dict of model_name → loaded (True/False)."""
        return {k: v is not None for k, v in cls._models.items()}
