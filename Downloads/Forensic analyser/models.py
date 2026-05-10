"""
Data models for AIVENTRA Forensic Analysis System
"""

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime


class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class BuildEnum(str, Enum):
    SLIM = "slim"
    MEDIUM = "medium"
    HEAVY = "heavy"
    ATHLETIC = "athletic"
    UNKNOWN = "unknown"


class ClothingTypeEnum(str, Enum):
    SHIRT = "shirt"
    JACKET = "jacket"
    PANTS = "pants"
    DRESS = "dress"
    OTHER = "other"
    UNKNOWN = "unknown"


class ClothingDescription(BaseModel):
    clothing_type: ClothingTypeEnum = ClothingTypeEnum.UNKNOWN
    color: Optional[str] = None
    pattern: Optional[str] = None
    description: Optional[str] = None


class VictimProfile(BaseModel):
    name: str
    age: Optional[int] = None
    gender: GenderEnum = GenderEnum.UNKNOWN
    height_cm: Optional[int] = None
    build: BuildEnum = BuildEnum.UNKNOWN
    distinguishing_marks: Optional[str] = None
    clothing: Optional[List[ClothingDescription]] = None
    additional_notes: Optional[str] = None


class SuspectProfile(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: GenderEnum = GenderEnum.UNKNOWN
    height_cm: Optional[int] = None
    build: BuildEnum = BuildEnum.UNKNOWN
    distinguishing_marks: Optional[str] = None
    behavioral_flags: Optional[List[str]] = None
    clothing: Optional[List[ClothingDescription]] = None
    additional_notes: Optional[str] = None


class IncidentDetails(BaseModel):
    incident_type: str = "unknown"
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None


class VideoMetadata(BaseModel):
    camera_id: str
    location: Optional[str] = None
    camera_latitude: Optional[float] = None
    camera_longitude: Optional[float] = None
    start_time: Optional[str] = None
    fps: int = 30


class ForensicAnalysisRequest(BaseModel):
    case_id: str
    victim_profile: VictimProfile
    suspect_profile: Optional[SuspectProfile] = None
    incident_details: IncidentDetails
    created_at: datetime = None

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        if data.get('created_at') is None:
            data['created_at'] = datetime.now()
        super().__init__(**data)
