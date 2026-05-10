"""
Track people across video frames and across multiple cameras
Uses 3-frame confirmation to eliminate false positives
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
from config import settings

logger = logging.getLogger(__name__)


@dataclass
class TrackedPerson:
    """Represents a confirmed tracked person"""
    person_id: str
    camera_id: str
    first_seen: datetime
    last_seen: datetime
    detections: List[dict]
    gait_samples: List[np.ndarray]
    victim_confidence: float = 0.0
    suspect_confidence: float = 0.0

    def add_detection(self, detection: dict):
        """Add a detection to this person"""
        self.detections.append(detection)
        self.last_seen = detection.get('timestamp', self.last_seen)

    def add_gait_sample(self, gait_vector: np.ndarray):
        """Add gait sample"""
        self.gait_samples.append(gait_vector)

    def get_best_detection(self) -> dict:
        """Get detection with highest confidence"""
        if not self.detections:
            return {}
        return max(self.detections, key=lambda x: x.get('confidence', 0))


class PersonTracker:
    """
    Track people across video frames with 3-frame confirmation.
    A detection must persist across MIN_CONFIRM_FRAMES consecutive frames
    to be considered a real person (eliminates false positives).
    """

    MIN_CONFIRM_FRAMES = 5       # Must appear 5+ times to confirm
    CENTROID_THRESHOLD = 500     # Max pixel distance to match same person
    MAX_SKIP_FRAMES = 150        # Drop person if unseen for this many frames

    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        # Confirmed people (passed 3-frame threshold)
        self.tracked_people: Dict[str, TrackedPerson] = {}
        # Candidates not yet confirmed
        self._candidates: Dict[str, dict] = {}
        self.next_person_id = 1
        self._frame_counter = 0

    def update_tracking(self, frame_idx: int, detections: List[dict],
                        timestamp: datetime) -> List[str]:
        """
        Update tracking with new detections.
        Returns list of CONFIRMED person IDs detected in this frame.
        """
        self._frame_counter = frame_idx

        if not detections:
            self._age_out_candidates()
            return []

        matched_person_ids = []
        matched_detection_indices = set()

        # --- Phase 1: Match against already-confirmed people ---
        for person_id, person in self.tracked_people.items():
            best_det = person.get_best_detection()
            if not best_det or 'box' not in best_det:
                continue

            last_box = best_det['box']
            last_cx = (last_box[0] + last_box[2]) / 2
            last_cy = (last_box[1] + last_box[3]) / 2

            best_match_idx, min_dist = self._find_closest(
                last_cx, last_cy, detections, matched_detection_indices
            )

            if best_match_idx >= 0:
                person.add_detection({
                    'box': detections[best_match_idx]['box'],
                    'crop': detections[best_match_idx].get('crop'),
                    'encoding': detections[best_match_idx].get('encoding'),
                    'confidence': detections[best_match_idx].get('confidence', 0.5),
                    'timestamp': timestamp,
                    'frame_idx': frame_idx
                })
                matched_person_ids.append(person_id)
                matched_detection_indices.add(best_match_idx)

        # --- Phase 2: Match remaining detections against candidates ---
        for cand_id, cand in list(self._candidates.items()):
            last_box = cand['last_box']
            last_cx = (last_box[0] + last_box[2]) / 2
            last_cy = (last_box[1] + last_box[3]) / 2

            best_match_idx, min_dist = self._find_closest(
                last_cx, last_cy, detections, matched_detection_indices
            )

            if best_match_idx >= 0:
                det = detections[best_match_idx]
                cand['count'] += 1
                cand['last_box'] = det['box']
                cand['last_frame'] = frame_idx
                cand['all_detections'].append({
                    'box': det['box'],
                    'crop': det.get('crop'),
                    'encoding': det.get('encoding'),
                    'confidence': det.get('confidence', 0.5),
                    'timestamp': timestamp,
                    'frame_idx': frame_idx
                })
                matched_detection_indices.add(best_match_idx)

                # Promote to confirmed if threshold met
                if cand['count'] >= self.MIN_CONFIRM_FRAMES:
                    person = TrackedPerson(
                        person_id=cand_id,
                        camera_id=self.camera_id,
                        first_seen=cand['first_seen'],
                        last_seen=timestamp,
                        detections=cand['all_detections'],
                        gait_samples=[]
                    )
                    self.tracked_people[cand_id] = person
                    del self._candidates[cand_id]
                    matched_person_ids.append(cand_id)
                    logger.info(f"Confirmed person {cand_id} after {cand['count']} detections")

        # --- Phase 3: Create new candidates from unmatched detections ---
        for idx, det in enumerate(detections):
            if idx not in matched_detection_indices:
                cand_id = f"{self.camera_id}_P{self.next_person_id}"
                self.next_person_id += 1
                self._candidates[cand_id] = {
                    'count': 1,
                    'last_box': det['box'],
                    'first_seen': timestamp,
                    'last_frame': frame_idx,
                    'all_detections': [{
                        'box': det['box'],
                        'crop': det.get('crop'),
                        'encoding': det.get('encoding'),
                        'confidence': det.get('confidence', 0.5),
                        'timestamp': timestamp,
                        'frame_idx': frame_idx
                    }]
                }

        # Age out stale candidates
        self._age_out_candidates()

        return matched_person_ids

    def _find_closest(self, cx: float, cy: float, detections: List[dict],
                      exclude: set) -> Tuple[int, float]:
        """Find closest detection to (cx, cy), return (index, distance)"""
        min_distance = float('inf')
        best_idx = -1

        for idx, det in enumerate(detections):
            if idx in exclude:
                continue
            box = det['box']
            dcx = (box[0] + box[2]) / 2
            dcy = (box[1] + box[3]) / 2
            dist = np.sqrt((cx - dcx) ** 2 + (cy - dcy) ** 2)

            if dist < self.CENTROID_THRESHOLD and dist < min_distance:
                min_distance = dist
                best_idx = idx

        return best_idx, min_distance

    def _age_out_candidates(self):
        """Remove candidates that haven't been seen recently"""
        to_remove = [
            cid for cid, c in self._candidates.items()
            if (self._frame_counter - c['last_frame']) > self.MAX_SKIP_FRAMES
        ]
        for cid in to_remove:
            del self._candidates[cid]

    def get_all_tracked_people(self) -> List[TrackedPerson]:
        """Get list of all CONFIRMED tracked people"""
        return list(self.tracked_people.values())

    def get_person(self, person_id: str) -> Optional[TrackedPerson]:
        """Get specific tracked person"""
        return self.tracked_people.get(person_id)


class MultiCameraTracker:
    """Track people across multiple cameras"""

    def __init__(self):
        self.camera_trackers: Dict[str, PersonTracker] = {}
        self.cross_camera_links: List[dict] = []

    def add_camera(self, camera_id: str):
        """Add new camera tracker"""
        if camera_id not in self.camera_trackers:
            self.camera_trackers[camera_id] = PersonTracker(camera_id)

    def update_camera_detections(self, camera_id: str, frame_idx: int,
                                 detections: List[dict], timestamp: datetime):
        """Update detections for specific camera"""
        if camera_id not in self.camera_trackers:
            self.add_camera(camera_id)

        return self.camera_trackers[camera_id].update_tracking(
            frame_idx, detections, timestamp
        )

    def link_cross_camera_people(self, person1_camera: str, person1_id: str,
                                 person2_camera: str, person2_id: str,
                                 similarity: float, time_gap_seconds: float):
        """Link same person detected in different cameras"""
        link = {
            'person1': {'camera': person1_camera, 'id': person1_id},
            'person2': {'camera': person2_camera, 'id': person2_id},
            'face_match_confidence': similarity * 100,
            'time_gap_seconds': time_gap_seconds,
            'feasible': True
        }
        self.cross_camera_links.append(link)

    def get_all_tracked_people_all_cameras(self) -> Dict[str, List[TrackedPerson]]:
        """Get all CONFIRMED tracked people from all cameras"""
        result = {}
        for camera_id, tracker in self.camera_trackers.items():
            result[camera_id] = tracker.get_all_tracked_people()
        return result