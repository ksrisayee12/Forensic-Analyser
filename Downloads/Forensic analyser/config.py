"""
Configuration settings for AIVENTRA Forensic Analysis System
"""

from pathlib import Path
from dataclasses import dataclass


@dataclass
class Settings:
    """Application settings"""
    # API
    API_TITLE: str = "AIVENTRA Forensic Analysis API"
    API_VERSION: str = "1.0.0"

    # Directories
    BASE_DIR: Path = Path(__file__).parent
    UPLOADS_DIR: Path = BASE_DIR / "uploads"
    VIDEOS_DIR: Path = BASE_DIR / "uploads" / "videos"
    PHOTOS_DIR: Path = BASE_DIR / "uploads" / "photos"
    OUTPUTS_DIR: Path = BASE_DIR / "outputs"

    # Limits
    MAX_VIDEO_SIZE_MB: int = 500
    MAX_PHOTO_SIZE_MB: int = 10
    MAX_VIDEOS_PER_ANALYSIS: int = 10

    # Processing
    FRAME_SKIP: int = 5  # Process every Nth frame
    FACE_DETECTION_CONFIDENCE: float = 0.5
    FACE_MATCH_THRESHOLD: float = 0.6
    MAX_TRACKING_ID_SKIP_FRAMES: int = 30

    # Pose
    POSE_CONFIDENCE_THRESHOLD: float = 0.5


settings = Settings()


def init_directories():
    """Create required directories if they don't exist"""
    settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    settings.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    settings.PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
