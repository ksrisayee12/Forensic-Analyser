"""
Pose Analyzer - Analyze body poses using MediaPipe (optional dependency)
Falls back to stub if MediaPipe is not available
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

from config import settings

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
    logger.info("MediaPipe available for pose analysis")
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not available, pose analysis disabled")


class PoseAnalyzer:
    """Analyze body poses in video frames"""

    def __init__(self):
        self.pose = None
        if MEDIAPIPE_AVAILABLE:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                min_detection_confidence=settings.POSE_CONFIDENCE_THRESHOLD,
                min_tracking_confidence=0.5
            )

    def analyze_pose(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Analyze pose in a frame.

        Returns dict with:
            - landmarks: list of (x, y, z, visibility) tuples
            - gait_vector: numpy array for gait signature
            - posture: estimated posture description
        """
        if not MEDIAPIPE_AVAILABLE or self.pose is None:
            return None

        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)

            if not results.pose_landmarks:
                return None

            landmarks = []
            for lm in results.pose_landmarks.landmark:
                landmarks.append({
                    'x': lm.x,
                    'y': lm.y,
                    'z': lm.z,
                    'visibility': lm.visibility
                })

            # Extract gait vector from key landmarks (hips, knees, ankles)
            gait_indices = [23, 24, 25, 26, 27, 28]  # Left/right hip, knee, ankle
            gait_vector = np.array([
                [landmarks[i]['x'], landmarks[i]['y']]
                for i in gait_indices if i < len(landmarks)
            ]).flatten()

            # Estimate posture
            posture = self._estimate_posture(landmarks)

            return {
                'landmarks': landmarks,
                'gait_vector': gait_vector,
                'posture': posture
            }
        except Exception as e:
            logger.error(f"Pose analysis error: {e}")
            return None

    def _estimate_posture(self, landmarks: List[Dict]) -> str:
        """Estimate general posture from landmarks"""
        try:
            if len(landmarks) < 29:
                return "unknown"

            # Check if person is standing, sitting, or lying
            left_hip_y = landmarks[23]['y']
            left_knee_y = landmarks[25]['y']
            left_ankle_y = landmarks[27]['y']
            nose_y = landmarks[0]['y']

            # Standing: nose well above hips, hips above knees
            if nose_y < left_hip_y and left_hip_y < left_knee_y:
                return "standing"
            elif abs(left_hip_y - left_knee_y) < 0.1:
                return "sitting"
            elif abs(nose_y - left_hip_y) < 0.1:
                return "lying_down"
            else:
                return "unknown"
        except (IndexError, KeyError):
            return "unknown"

    def extract_gait_signature(self, frames_poses: List[Dict]) -> Optional[np.ndarray]:
        """Extract overall gait signature from multiple frame poses"""
        gait_vectors = [
            p['gait_vector'] for p in frames_poses
            if p and 'gait_vector' in p and p['gait_vector'] is not None
        ]

        if not gait_vectors:
            return None

        # Average gait vector
        return np.mean(gait_vectors, axis=0)

    def close(self):
        """Release resources"""
        if self.pose:
            self.pose.close()
            self.pose = None
