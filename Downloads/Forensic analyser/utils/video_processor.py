"""
Video Processor - Extract and process frames from video files
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, Optional
from datetime import datetime, timedelta
import logging

from config import settings

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process video files for forensic analysis"""

    def __init__(self, video_path: str, camera_id: str, start_time: datetime, fps: int = 30):
        self.video_path = video_path
        self.camera_id = camera_id
        self.start_time = start_time
        self.fps = fps
        self.cap = None
        self.total_frames = 0
        self.frame_width = 0
        self.frame_height = 0

    def open(self) -> bool:
        """Open video file"""
        try:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                logger.error(f"Failed to open video: {self.video_path}")
                return False

            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            if actual_fps > 0:
                self.fps = int(actual_fps)

            logger.info(
                f"Opened video: {self.video_path} | "
                f"{self.frame_width}x{self.frame_height} | "
                f"{self.total_frames} frames @ {self.fps}fps"
            )
            return True
        except Exception as e:
            logger.error(f"Error opening video {self.video_path}: {e}")
            return False

    def extract_frames(self, frame_skip: int = None) -> Generator[Tuple[int, np.ndarray, datetime], None, None]:
        """
        Extract frames from video with optional frame skipping.

        Yields:
            (frame_index, frame_array, timestamp)
        """
        if not self.cap or not self.cap.isOpened():
            if not self.open():
                return

        skip = frame_skip if frame_skip else settings.FRAME_SKIP
        frame_idx = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            if frame_idx % skip == 0:
                timestamp = self.start_time + timedelta(seconds=frame_idx / self.fps)
                yield frame_idx, frame, timestamp

            frame_idx += 1

    def get_frame_at(self, frame_idx: int) -> Optional[np.ndarray]:
        """Get a specific frame by index"""
        if not self.cap or not self.cap.isOpened():
            if not self.open():
                return None

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = self.cap.read()
        return frame if ret else None

    def close(self):
        """Release video capture"""
        if self.cap:
            self.cap.release()
            self.cap = None

    def __del__(self):
        self.close()
