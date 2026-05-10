"""
Behavior Detector - Detect suspicious behaviors from pose and movement data
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BehaviorDetector:
    """Detect suspicious or notable behaviors from analysis data"""

    def __init__(self):
        self.behavior_log: List[Dict] = []

    def analyze_movement(self, person_id: str, detections: List[Dict],
                         camera_id: str) -> List[Dict]:
        """
        Analyze movement patterns for suspicious behavior.

        Returns list of detected behaviors with timestamps
        """
        behaviors = []

        if len(detections) < 2:
            return behaviors

        # Check for loitering (person stays in similar position for extended time)
        loiter = self._check_loitering(person_id, detections, camera_id)
        if loiter:
            behaviors.append(loiter)

        # Check for erratic movement
        erratic = self._check_erratic_movement(person_id, detections, camera_id)
        if erratic:
            behaviors.append(erratic)

        # Check for sudden running
        running = self._check_running(person_id, detections, camera_id)
        if running:
            behaviors.append(running)

        self.behavior_log.extend(behaviors)
        return behaviors

    def _check_loitering(self, person_id: str, detections: List[Dict],
                          camera_id: str) -> Optional[Dict]:
        """Check if person is loitering (staying in same area)"""
        if len(detections) < 5:
            return None

        # Calculate position variance
        positions = []
        for det in detections:
            box = det.get('box', (0, 0, 0, 0))
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            positions.append((cx, cy))

        positions = np.array(positions)
        variance = np.var(positions, axis=0).sum()

        # Low variance = loitering
        if variance < 500:
            first_ts = detections[0].get('timestamp', datetime.now())
            last_ts = detections[-1].get('timestamp', datetime.now())

            return {
                'type': 'loitering',
                'person_id': person_id,
                'camera_id': camera_id,
                'confidence': min(0.9, 1.0 - variance / 500),
                'start_time': first_ts.isoformat() if isinstance(first_ts, datetime) else str(first_ts),
                'end_time': last_ts.isoformat() if isinstance(last_ts, datetime) else str(last_ts),
                'description': f"Person {person_id} loitering with low movement variance ({variance:.1f})"
            }
        return None

    def _check_erratic_movement(self, person_id: str, detections: List[Dict],
                                 camera_id: str) -> Optional[Dict]:
        """Check for erratic/unusual movement patterns"""
        if len(detections) < 3:
            return None

        # Calculate direction changes
        positions = []
        for det in detections:
            box = det.get('box', (0, 0, 0, 0))
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            positions.append((cx, cy))

        direction_changes = 0
        for i in range(2, len(positions)):
            dx1 = positions[i - 1][0] - positions[i - 2][0]
            dy1 = positions[i - 1][1] - positions[i - 2][1]
            dx2 = positions[i][0] - positions[i - 1][0]
            dy2 = positions[i][1] - positions[i - 1][1]

            # Check sign change (direction reversal)
            if (dx1 * dx2 < 0) or (dy1 * dy2 < 0):
                direction_changes += 1

        ratio = direction_changes / (len(positions) - 2)
        if ratio > 0.6:
            return {
                'type': 'erratic_movement',
                'person_id': person_id,
                'camera_id': camera_id,
                'confidence': min(0.85, ratio),
                'start_time': detections[0].get('timestamp', ''),
                'description': f"Person {person_id} showing erratic movement ({direction_changes} direction changes)"
            }
        return None

    def _check_running(self, person_id: str, detections: List[Dict],
                        camera_id: str) -> Optional[Dict]:
        """Check for sudden running (large displacements between frames)"""
        if len(detections) < 2:
            return None

        max_displacement = 0
        max_idx = 0

        for i in range(1, len(detections)):
            box1 = detections[i - 1].get('box', (0, 0, 0, 0))
            box2 = detections[i].get('box', (0, 0, 0, 0))
            cx1, cy1 = (box1[0] + box1[2]) / 2, (box1[1] + box1[3]) / 2
            cx2, cy2 = (box2[0] + box2[2]) / 2, (box2[1] + box2[3]) / 2

            displacement = np.sqrt((cx2 - cx1) ** 2 + (cy2 - cy1) ** 2)
            if displacement > max_displacement:
                max_displacement = displacement
                max_idx = i

        if max_displacement > 100:  # Significant displacement threshold
            return {
                'type': 'running',
                'person_id': person_id,
                'camera_id': camera_id,
                'confidence': min(0.8, max_displacement / 200),
                'timestamp': detections[max_idx].get('timestamp', ''),
                'description': f"Person {person_id} running detected (displacement: {max_displacement:.1f}px)"
            }
        return None

    def get_all_behaviors(self) -> List[Dict]:
        """Get all detected behaviors"""
        return self.behavior_log
