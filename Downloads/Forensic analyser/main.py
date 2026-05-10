"""
AIVENTRA FastAPI Application
Forensic Video Analysis System - No Hardcoding
"""

import logging
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import json
import uvicorn

from config import settings, init_directories
from models import (
    ForensicAnalysisRequest, VictimProfile, SuspectProfile,
    IncidentDetails, ClothingDescription, GenderEnum, BuildEnum, ClothingTypeEnum
)
from services.forensic_analyzer import ForensicAnalysisEngine

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AIVENTRA: AI-Powered Forensic Triage & Postmortem Intelligence System"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active analyses
active_analyses = {}

# ===================== HEALTH CHECK =====================

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "status": "online",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ===================== VICTIM PROFILE ENDPOINTS =====================

@app.post("/api/v1/victim-profile")
async def create_victim_profile(
    name: str = Form(...),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form("unknown"),
    height_cm: Optional[int] = Form(None),
    build: Optional[str] = Form("unknown"),
    distinguishing_marks: Optional[str] = Form(None),
    additional_notes: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    """
    Create victim profile
    All fields from form input - NO HARDCODING
    """
    try:
        # Validate inputs
        if not name or len(name) < 1:
            raise HTTPException(status_code=400, detail="Victim name required")
        
        # Parse enum values safely
        gender_enum = GenderEnum(gender) if gender in [e.value for e in GenderEnum] else GenderEnum.UNKNOWN
        build_enum = BuildEnum(build) if build in [e.value for e in BuildEnum] else BuildEnum.UNKNOWN
        
        # Create profile
        victim_profile = VictimProfile(
            name=name,
            age=age,
            gender=gender_enum,
            height_cm=height_cm,
            build=build_enum,
            distinguishing_marks=distinguishing_marks,
            additional_notes=additional_notes
        )
        
        # Save photo if provided
        photo_path = None
        if photo:
            if photo.size > settings.MAX_PHOTO_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Photo too large")
            
            photo_path = settings.PHOTOS_DIR / f"victim_{name}_{datetime.now().timestamp()}.jpg"
            with open(photo_path, "wb") as f:
                f.write(photo.file.read())
        
        return {
            "status": "success",
            "victim_profile": victim_profile.dict(),
            "photo_saved": photo_path is not None,
            "photo_path": str(photo_path) if photo_path else None
        }
    
    except Exception as e:
        logger.error(f"Error creating victim profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== SUSPECT PROFILE ENDPOINTS =====================

@app.post("/api/v1/suspect-profile")
async def create_suspect_profile(
    name: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form("unknown"),
    height_cm: Optional[int] = Form(None),
    build: Optional[str] = Form("unknown"),
    distinguishing_marks: Optional[str] = Form(None),
    behavioral_flags: Optional[str] = Form(None),
    additional_notes: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    """
    Create suspect profile - OPTIONAL
    All fields from form input - NO HARDCODING
    """
    try:
        gender_enum = GenderEnum(gender) if gender in [e.value for e in GenderEnum] else GenderEnum.UNKNOWN
        build_enum = BuildEnum(build) if build in [e.value for e in BuildEnum] else BuildEnum.UNKNOWN
        
        # Parse behavioral flags
        behavioral_list = []
        if behavioral_flags:
            behavioral_list = [f.strip() for f in behavioral_flags.split(',')]
        
        suspect_profile = SuspectProfile(
            name=name,
            age=age,
            gender=gender_enum,
            height_cm=height_cm,
            build=build_enum,
            distinguishing_marks=distinguishing_marks,
            behavioral_flags=behavioral_list if behavioral_list else None,
            additional_notes=additional_notes
        )
        
        # Save photo if provided
        photo_path = None
        if photo:
            if photo.size > settings.MAX_PHOTO_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Photo too large")
            
            suspect_name = name if name else "unknown"
            photo_path = settings.PHOTOS_DIR / f"suspect_{suspect_name}_{datetime.now().timestamp()}.jpg"
            with open(photo_path, "wb") as f:
                f.write(photo.file.read())
        
        return {
            "status": "success",
            "suspect_profile": suspect_profile.dict(),
            "photo_saved": photo_path is not None,
            "photo_path": str(photo_path) if photo_path else None
        }
    
    except Exception as e:
        logger.error(f"Error creating suspect profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== VIDEO UPLOAD ENDPOINTS =====================

@app.post("/api/v1/upload-videos")
async def upload_videos(
    case_id: str = Form(...),
    files: List[UploadFile] = File(...),
    camera_ids: str = Form(...),  # Comma-separated
    locations: str = Form(...),    # Comma-separated
    start_times: str = Form(...),  # ISO format, comma-separated
):
    """
    Upload multiple CCTV videos
    All metadata from form input - NO HARDCODING
    
    Args:
        case_id: Case identifier
        files: Video files
        camera_ids: Comma-separated camera IDs (e.g., "CAM_001,CAM_002")
        locations: Comma-separated locations (e.g., "Main Street,Back Alley")
        start_times: Comma-separated ISO timestamps (e.g., "2024-05-09T14:00:00,2024-05-09T14:05:00")
    """
    try:
        # Parse inputs
        cam_ids = [c.strip() for c in camera_ids.split(',')]
        locs = [l.strip() for l in locations.split(',')]
        times = [datetime.fromisoformat(t.strip()) for t in start_times.split(',')]
        
        # Validate counts match
        if len(files) != len(cam_ids) or len(files) != len(locs) or len(files) != len(times):
            raise HTTPException(
                status_code=400,
                detail="Number of videos must match camera_ids, locations, and start_times"
            )
        
        # Check max videos
        if len(files) > settings.MAX_VIDEOS_PER_ANALYSIS:
            raise HTTPException(
                status_code=400,
                detail=f"Maximum {settings.MAX_VIDEOS_PER_ANALYSIS} videos per analysis"
            )
        
        # Save videos and store metadata
        saved_videos = []
        video_list = []
        
        for idx, (file, cam_id, location, start_time) in enumerate(zip(files, cam_ids, locs, times)):
            # Validate file
            if not file.filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid video format: {file.filename}. Allowed: mp4, avi, mov, mkv"
                )
            
            # Check file size
            file_size = len(file.file.read()) / (1024 * 1024)
            file.file.seek(0)
            
            if file_size > settings.MAX_VIDEO_SIZE_MB:
                raise HTTPException(
                    status_code=400,
                    detail=f"Video {file.filename} too large ({file_size:.1f}MB). Max: {settings.MAX_VIDEO_SIZE_MB}MB"
                )
            
            # Save file
            video_path = settings.VIDEOS_DIR / f"{case_id}_{cam_id}_{datetime.now().timestamp()}.mp4"
            with open(video_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            saved_videos.append({
                'original_filename': file.filename,
                'saved_path': str(video_path),
                'camera_id': cam_id,
                'location': location,
                'start_time': start_time.isoformat(),
                'file_size_mb': f"{file_size:.2f}"
            })
            
            video_list.append({
                'path': str(video_path),
                'camera_id': cam_id,
                'location': location,
                'start_time': start_time,
                'fps': 30  # Default, can be updated
            })
        
        return {
            "status": "success",
            "case_id": case_id,
            "videos_uploaded": len(saved_videos),
            "uploaded_videos": saved_videos
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===================== ANALYSIS ENDPOINTS =====================

@app.post("/api/v1/start-analysis")
async def start_analysis(
    case_id: str = Form(...),
    victim_profile_json: str = Form(...),
    incident_details_json: str = Form(...),
    suspect_profile_json: Optional[str] = Form(None),
    victim_photo_path: Optional[str] = Form(None),
    suspect_photo_path: Optional[str] = Form(None),
    video_paths_json: str = Form(...),  # JSON list of video metadata
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Start forensic analysis
    All data from form input - NO HARDCODING
    
    Args:
        case_id: Case identifier
        victim_profile_json: JSON string of victim profile
        incident_details_json: JSON string of incident details
        suspect_profile_json: JSON string of suspect profile (optional)
        victim_photo_path: Path to victim photo
        suspect_photo_path: Path to suspect photo
        video_paths_json: JSON list of video metadata
    """
    try:
        # Check if case already being analyzed
        if case_id in active_analyses:
            return {
                "status": "already_processing",
                "case_id": case_id,
                "message": "Analysis for this case is already in progress"
            }
        
        # Parse JSON inputs
        victim_data = json.loads(victim_profile_json)
        incident_data = json.loads(incident_details_json)
        video_data = json.loads(video_paths_json)
        
        suspect_data = None
        if suspect_profile_json:
            try:
                suspect_data = json.loads(suspect_profile_json)
            except:
                suspect_data = None
        
        # Create profiles from JSON
        victim_profile = VictimProfile(**victim_data)
        
        suspect_profile = None
        if suspect_data:
            suspect_profile = SuspectProfile(**suspect_data)
        
        incident_details = IncidentDetails(**incident_data)
        
        # Create analysis request
        analysis_request = ForensicAnalysisRequest(
            case_id=case_id,
            victim_profile=victim_profile,
            suspect_profile=suspect_profile,
            incident_details=incident_details
        )
        
        # Create analysis engine
        engine = ForensicAnalysisEngine(analysis_request)
        
        # Add photos if provided
        if victim_photo_path:
            success, msg = engine.add_victim_photo(victim_photo_path)
            if not success:
                logger.warning(f"Failed to add victim photo: {msg}")
        
        if suspect_photo_path:
            success, msg = engine.add_suspect_photo(suspect_photo_path)
            if not success:
                logger.warning(f"Failed to add suspect photo: {msg}")
        
        # Mark as active
        active_analyses[case_id] = {
            'status': 'processing',
            'start_time': datetime.now().isoformat(),
            'engine': engine
        }
        
        # Run analysis in background
        background_tasks.add_task(
            _run_analysis,
            case_id,
            engine,
            video_data
        )
        
        return {
            "status": "analysis_started",
            "case_id": case_id,
            "message": "Analysis started in background",
            "videos_to_analyze": len(video_data)
        }
    
    except Exception as e:
        logger.error(f"Error starting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_analysis(case_id: str, engine: ForensicAnalysisEngine, video_list: List[dict]):
    """Run analysis in background"""
    try:
        logger.info(f"Starting background analysis for case {case_id}")
        
        # Run analysis
        results = engine.analyze_videos(video_list)
        
        # Update active analyses
        active_analyses[case_id]['status'] = 'completed'
        active_analyses[case_id]['results'] = results
        active_analyses[case_id]['end_time'] = datetime.now().isoformat()
        
        logger.info(f"Analysis completed for case {case_id}")
    
    except Exception as e:
        logger.error(f"Error in background analysis: {e}")
        active_analyses[case_id]['status'] = 'failed'
        active_analyses[case_id]['error'] = str(e)
    
    finally:
        engine.cleanup()

@app.get("/api/v1/analysis-status/{case_id}")
async def get_analysis_status(case_id: str):
    """Get analysis status"""
    if case_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Case not found")
    
    analysis = active_analyses[case_id]
    
    return {
        "case_id": case_id,
        "status": analysis['status'],
        "start_time": analysis.get('start_time'),
        "end_time": analysis.get('end_time'),
        "results": analysis.get('results') if analysis['status'] == 'completed' else None,
        "error": analysis.get('error') if analysis['status'] == 'failed' else None
    }

@app.get("/api/v1/analysis-results/{case_id}")
async def get_analysis_results(case_id: str):
    """Get analysis results"""
    if case_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Case not found")
    
    analysis = active_analyses[case_id]
    
    if analysis['status'] != 'completed':
        raise HTTPException(status_code=400, detail=f"Analysis status: {analysis['status']}")
    
    return analysis.get('results', {})

# ===================== REPORT DOWNLOAD ENDPOINTS =====================

@app.get("/api/v1/reports/{case_id}")
async def list_reports(case_id: str):
    """List all generated reports for case"""
    report_dir = settings.OUTPUTS_DIR / case_id
    
    if not report_dir.exists():
        raise HTTPException(status_code=404, detail="No reports found for this case")
    
    csv_files = list(report_dir.glob('*.csv'))
    
    return {
        "case_id": case_id,
        "reports_count": len(csv_files),
        "reports": [
            {
                'filename': f.name,
                'path': f"/api/v1/download-report/{case_id}/{f.name}",
                'size_mb': f.stat().st_size / (1024 * 1024)
            }
            for f in csv_files
        ]
    }

@app.get("/api/v1/download-report/{case_id}/{report_filename}")
async def download_report(case_id: str, report_filename: str):
    """Download specific report CSV"""
    report_path = settings.OUTPUTS_DIR / case_id / report_filename
    
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=report_path,
        filename=report_filename,
        media_type='text/csv'
    )

# ===================== UTILITY ENDPOINTS =====================

@app.get("/api/v1/case-info/{case_id}")
async def get_case_info(case_id: str):
    """Get case information"""
    if case_id not in active_analyses:
        raise HTTPException(status_code=404, detail="Case not found")
    
    analysis = active_analyses[case_id]
    
    return {
        "case_id": case_id,
        "status": analysis['status'],
        "created_at": analysis.get('start_time'),
        "videos_to_analyze": analysis.get('video_count'),
        "reports_generated": analysis.get('results', {}).get('reports_generated') if analysis['status'] == 'completed' else []
    }

# ===================== MAIN =====================

if __name__ == "__main__":
    init_directories()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
