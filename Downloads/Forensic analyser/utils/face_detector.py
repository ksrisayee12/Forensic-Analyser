"""
Face Detector - Detect and encode faces using face_recognition library
Falls back to OpenCV Haar Cascade if face_recognition is not available
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Try importing face_recognition; fall back to OpenCV
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    logger.info("face_recognition library available")
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning("face_recognition not available, using OpenCV Haar Cascade fallback")


class FaceDetector:
    """Detect and recognize faces in frames"""

    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self._cascade = None

        if not FACE_RECOGNITION_AVAILABLE:
            # Load Haar Cascade as fallback
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._cascade = cv2.CascadeClassifier(cascade_path)

    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect faces in a frame.

        Returns list of dicts with:
            - box: (top, right, bottom, left)
            - crop: cropped face image
            - encoding: face encoding (if face_recognition available)
            - confidence: detection confidence
        """
        if FACE_RECOGNITION_AVAILABLE:
            return self._detect_with_face_recognition(frame)
        else:
            return self._detect_with_haar(frame)

    def _detect_with_face_recognition(self, frame: np.ndarray) -> List[Dict]:
        """Detect using face_recognition library"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.5, fy=0.5)

        locations = face_recognition.face_locations(small_frame, model="hog")
        encodings = face_recognition.face_encodings(small_frame, locations)

        results = []
        for (top, right, bottom, left), encoding in zip(locations, encodings):
            # Scale back to original size
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            # Crop face
            crop = frame[max(0, top):bottom, max(0, left):right]

            results.append({
                'box': (top, right, bottom, left),
                'crop': crop,
                'encoding': encoding,
                'confidence': 0.9
            })

        return results

    def _detect_with_haar(self, frame: np.ndarray) -> List[Dict]:
        """Detect using OpenCV Haar Cascade (fallback)"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self._cascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=8,
            minSize=(60, 60)
        )

        results = []
        for (x, y, w, h) in faces:
            top, right, bottom, left = y, x + w, y + h, x
            crop = frame[top:bottom, left:right]

            results.append({
                'box': (top, right, bottom, left),
                'crop': crop,
                'encoding': None,
                'confidence': 0.7
            })

        return results

    def compare_faces(self, known_encoding: np.ndarray, face_encoding: np.ndarray,
                      tolerance: float = 0.6) -> Tuple[bool, float]:
        """
        Compare two face encodings.

        Returns:
            (match: bool, distance: float)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return False, 1.0

        if known_encoding is None or face_encoding is None:
            return False, 1.0

        distance = face_recognition.face_distance([known_encoding], face_encoding)[0]
        match = distance <= tolerance
        return match, float(distance)

    def encode_face_from_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load image and get face encoding"""
        if not FACE_RECOGNITION_AVAILABLE:
            logger.warning("Cannot encode face: face_recognition not available")
            return None

        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                return encodings[0]
            logger.warning(f"No faces found in image: {image_path}")
            return None
        except Exception as e:
            logger.error(f"Error encoding face from {image_path}: {e}")
            return None
