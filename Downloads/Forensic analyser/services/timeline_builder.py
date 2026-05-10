"""
Timeline Builder - Build event timelines from analysis data
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TimelineBuilder:
    """Build chronological event timelines from forensic analysis"""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.events: List[Dict] = []

    def add_event(self, timestamp, camera_id: str, person_id: str,
                  event_type: str, location: str = "", confidence: float = 0.0,
                  description: str = ""):
        """Add an event to the timeline"""
        ts_str = timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp)
        self.events.append({
            'timestamp': ts_str,
            'camera_id': camera_id,
            'person_id': person_id,
            'event_type': event_type,
            'location': location,
            'confidence': confidence,
            'description': description
        })

    def add_person_first_seen(self, person_id: str, camera_id: str,
                               timestamp, location: str = ""):
        """Record when a person was first seen"""
        self.add_event(
            timestamp=timestamp,
            camera_id=camera_id,
            person_id=person_id,
            event_type='first_seen',
            location=location,
            description=f"Person {person_id} first detected on {camera_id}"
        )

    def add_person_last_seen(self, person_id: str, camera_id: str,
                              timestamp, location: str = ""):
        """Record when a person was last seen"""
        self.add_event(
            timestamp=timestamp,
            camera_id=camera_id,
            person_id=person_id,
            event_type='last_seen',
            location=location,
            description=f"Person {person_id} last detected on {camera_id}"
        )

    def add_behavior_event(self, behavior: Dict):
        """Add a behavior detection event"""
        self.add_event(
            timestamp=behavior.get('start_time', behavior.get('timestamp', '')),
            camera_id=behavior.get('camera_id', ''),
            person_id=behavior.get('person_id', ''),
            event_type=f"behavior_{behavior.get('type', 'unknown')}",
            confidence=behavior.get('confidence', 0),
            description=behavior.get('description', '')
        )

    def add_cross_camera_link(self, link: Dict):
        """Add cross-camera identification event"""
        p1 = link.get('person1', {})
        p2 = link.get('person2', {})
        self.add_event(
            timestamp=datetime.now(),
            camera_id=f"{p1.get('camera', '')} -> {p2.get('camera', '')}",
            person_id=f"{p1.get('id', '')} / {p2.get('id', '')}",
            event_type='cross_camera_match',
            confidence=link.get('face_match_confidence', 0),
            description=f"Cross-camera match (gap: {link.get('time_gap_seconds', 0):.1f}s)"
        )

    def build_timeline(self) -> List[Dict]:
        """Get sorted timeline events"""
        return sorted(self.events, key=lambda e: e.get('timestamp', ''))

    def get_events_for_person(self, person_id: str) -> List[Dict]:
        """Get timeline events for a specific person"""
        return sorted(
            [e for e in self.events if e['person_id'] == person_id],
            key=lambda e: e.get('timestamp', '')
        )
