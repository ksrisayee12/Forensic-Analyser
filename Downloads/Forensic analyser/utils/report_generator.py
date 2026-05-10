"""
Report Generator - Generate CSV reports from forensic analysis results
"""

import csv
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging

from config import settings

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generate forensic analysis reports as CSV files"""

    def __init__(self, case_id: str):
        self.case_id = case_id
        self.output_dir = settings.OUTPUTS_DIR / case_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_timeline_report(self, timeline_events: List[Dict]) -> str:
        """Generate CSV timeline report"""
        report_path = self.output_dir / f"{self.case_id}_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        fieldnames = ['timestamp', 'camera_id', 'person_id', 'event_type',
                       'location', 'confidence', 'description']

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for event in timeline_events:
                row = {k: event.get(k, '') for k in fieldnames}
                writer.writerow(row)

        logger.info(f"Timeline report saved: {report_path}")
        return str(report_path)

    def generate_persons_report(self, tracked_persons: Dict[str, List]) -> str:
        """Generate CSV report of all tracked persons"""
        report_path = self.output_dir / f"{self.case_id}_persons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        fieldnames = ['person_id', 'camera_id', 'first_seen', 'last_seen',
                       'total_detections', 'victim_confidence', 'suspect_confidence']

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for camera_id, persons in tracked_persons.items():
                for person in persons:
                    writer.writerow({
                        'person_id': person.person_id,
                        'camera_id': camera_id,
                        'first_seen': person.first_seen.isoformat() if isinstance(person.first_seen, datetime) else str(person.first_seen),
                        'last_seen': person.last_seen.isoformat() if isinstance(person.last_seen, datetime) else str(person.last_seen),
                        'total_detections': len(person.detections),
                        'victim_confidence': f"{person.victim_confidence:.2f}",
                        'suspect_confidence': f"{person.suspect_confidence:.2f}"
                    })

        logger.info(f"Persons report saved: {report_path}")
        return str(report_path)

    def generate_behavior_report(self, behaviors: List[Dict]) -> str:
        """Generate CSV report of detected behaviors"""
        report_path = self.output_dir / f"{self.case_id}_behaviors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        fieldnames = ['type', 'person_id', 'camera_id', 'confidence',
                       'start_time', 'end_time', 'timestamp', 'description']

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for behavior in behaviors:
                row = {k: behavior.get(k, '') for k in fieldnames}
                writer.writerow(row)

        logger.info(f"Behavior report saved: {report_path}")
        return str(report_path)

    def generate_gap_report(self, gaps: List[Dict]) -> str:
        """Generate CSV report of gap analysis results"""
        report_path = self.output_dir / f"{self.case_id}_gaps_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        fieldnames = [
            'last_seen_camera', 'last_seen_time',
            'reappeared_camera', 'reappeared_time',
            'gap_minutes', 'gap_seconds',
            'distance_km', 'required_walking_time_min',
            'is_suspicious', 'suspicion_reason',
            'risk_score', 'possibilities'
        ]

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for gap in gaps:
                row = {k: gap.get(k, '') for k in fieldnames}
                # Convert list to string for CSV
                if isinstance(row.get('possibilities'), list):
                    row['possibilities'] = ' | '.join(row['possibilities'])
                writer.writerow(row)

        logger.info(f"Gap analysis report saved: {report_path}")
        return str(report_path)

    def generate_summary_report(self, analysis_summary: Dict) -> str:
        """Generate overall analysis summary CSV"""
        report_path = self.output_dir / f"{self.case_id}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(report_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Field', 'Value'])
            writer.writerow(['Case ID', self.case_id])
            writer.writerow(['Analysis Date', datetime.now().isoformat()])
            writer.writerow(['Total Videos Analyzed', analysis_summary.get('total_videos', 0)])
            writer.writerow(['Total Persons Detected', analysis_summary.get('total_persons', 0)])
            writer.writerow(['Total Behaviors Detected', analysis_summary.get('total_behaviors', 0)])
            writer.writerow(['Victim Matches Found', analysis_summary.get('victim_matches', 0)])
            writer.writerow(['Suspect Matches Found', analysis_summary.get('suspect_matches', 0)])
            writer.writerow(['Cross-Camera Links', analysis_summary.get('cross_camera_links', 0)])
            writer.writerow(['Total Gaps Detected', analysis_summary.get('total_gaps', 0)])
            writer.writerow(['Suspicious Gaps', analysis_summary.get('suspicious_gaps', 0)])

        logger.info(f"Summary report saved: {report_path}")
        return str(report_path)

    def get_generated_reports(self) -> List[str]:
        """List all generated report files"""
        return [str(f) for f in self.output_dir.glob('*.csv')]
