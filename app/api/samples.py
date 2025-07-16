import shutil
import uuid
import time
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.auth import get_current_user, get_db
from app.models import Sample, User
from app.schemas.sample import (
    SampleCreate, SampleUpdate, SampleOut, SampleList, 
    SampleFilter, SampleUploadResponse, SampleAnalysis,
    CategoriesResponse, TagsResponse
)
from app.lib.audio.sample_analysis import SampleAnalyzer

router = APIRouter()

# Sample upload directory
SAMPLE_UPLOAD_DIR = Path("/tmp/sample_uploads")
SAMPLE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize analyzer
sample_analyzer = SampleAnalyzer()


@router.post("/samples/upload", response_model=SampleUploadResponse)
async def upload_sample(
    file: UploadFile = File(...),
    name: str = Query(..., description="Sample name"),
    description: Optional[str] = Query(None, description="Sample description"),
    category: str = Query(..., description="Sample category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload and analyze a new audio sample.
    """
    # Validate file type
    if file.content_type not in ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/flac"]:
        raise HTTPException(status_code=400, detail="Unsupported audio file format")
    
    # Validate category
    valid_categories = ["musical", "ambient", "percussion", "fx", "voice"]
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category. Must be one of: {valid_categories}")
    
    start_time = time.time()
    
    try:
        # Save file with unique name
        ext = Path(file.filename).suffix
        file_id = f"{uuid.uuid4()}{ext}"
        file_path = SAMPLE_UPLOAD_DIR / file_id
        
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Analyze the sample
        file.file.seek(0)
        analysis = sample_analyzer.analyze_sample(str(file_path))
        
        # Create sample record
        sample = Sample(
            user_id=current_user.id,
            name=name,
            description=description,
            category=category,
            filename=file.filename,
            file_path=str(file_path),
            content_type=file.content_type,
            size=analysis.get("size"),
            
            # Audio properties
            duration_sec=analysis.get("duration_sec"),
            sample_rate=analysis.get("sample_rate"),
            channels=analysis.get("channels", 1),
            
            # Musical features
            tempo_bpm=analysis.get("tempo_bpm"),
            key_signature=analysis.get("key_signature"),
            time_signature=analysis.get("time_signature"),
            
            # AI-relevant features
            spectral_centroid=analysis.get("spectral_centroid"),
            spectral_rolloff=analysis.get("spectral_rolloff"),
            zero_crossing_rate=analysis.get("zero_crossing_rate"),
            mfcc_features=analysis.get("mfcc_features"),
            rhythm_pattern=analysis.get("rhythm_pattern"),
            harmonic_content=analysis.get("harmonic_content"),
            
            # Perceptual features
            loudness=analysis.get("loudness"),
            energy=analysis.get("energy"),
            complexity=analysis.get("complexity"),
            intensity=analysis.get("intensity"),
            
            # Classification
            tags=analysis.get("tags"),
            mood=analysis.get("mood"),
            genre=analysis.get("genre"),
        )
        
        db.add(sample)
        db.commit()
        db.refresh(sample)
        
        analysis_time = time.time() - start_time
        
        return SampleUploadResponse(
            sample=sample,
            analysis_time=analysis_time,
            message="Sample uploaded and analyzed successfully"
        )
        
    except Exception as e:
        # Clean up file if it was created
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to upload sample: {str(e)}")


@router.get("/samples", response_model=SampleList)
def get_samples(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    mood: Optional[str] = Query(None, description="Filter by mood"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    min_duration: Optional[float] = Query(None, ge=0, description="Minimum duration in seconds"),
    max_duration: Optional[float] = Query(None, ge=0, description="Maximum duration in seconds"),
    min_tempo: Optional[float] = Query(None, ge=0, description="Minimum tempo BPM"),
    max_tempo: Optional[float] = Query(None, ge=0, description="Maximum tempo BPM"),
    key_signature: Optional[str] = Query(None, description="Filter by key signature"),
    min_energy: Optional[float] = Query(None, ge=0, le=1, description="Minimum energy (0-1)"),
    max_energy: Optional[float] = Query(None, ge=0, le=1, description="Maximum energy (0-1)"),
    min_intensity: Optional[float] = Query(None, ge=0, le=1, description="Minimum intensity (0-1)"),
    max_intensity: Optional[float] = Query(None, ge=0, le=1, description="Maximum intensity (0-1)"),
    is_generated: Optional[bool] = Query(None, description="Filter by generation status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of user's samples with filtering options.
    """
    # Build query
    query = db.query(Sample).filter(Sample.user_id == current_user.id)
    
    # Apply filters
    if category:
        query = query.filter(Sample.category == category)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        # Filter samples that contain any of the specified tags
        for tag in tag_list:
            query = query.filter(Sample.tags.contains([tag]))
    
    if mood:
        query = query.filter(Sample.mood == mood)
    
    if genre:
        query = query.filter(Sample.genre == genre)
    
    if min_duration is not None:
        query = query.filter(Sample.duration_sec >= min_duration)
    
    if max_duration is not None:
        query = query.filter(Sample.duration_sec <= max_duration)
    
    if min_tempo is not None:
        query = query.filter(Sample.tempo_bpm >= min_tempo)
    
    if max_tempo is not None:
        query = query.filter(Sample.tempo_bpm <= max_tempo)
    
    if key_signature:
        query = query.filter(Sample.key_signature == key_signature)
    
    if min_energy is not None:
        query = query.filter(Sample.energy >= min_energy)
    
    if max_energy is not None:
        query = query.filter(Sample.energy <= max_energy)
    
    if min_intensity is not None:
        query = query.filter(Sample.intensity >= min_intensity)
    
    if max_intensity is not None:
        query = query.filter(Sample.intensity <= max_intensity)
    
    if is_generated is not None:
        query = query.filter(Sample.is_generated == (1 if is_generated else 0))
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Sample.name.ilike(search_term),
                Sample.description.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    samples = query.offset(offset).limit(per_page).all()
    
    return SampleList(
        samples=samples,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/samples/categories")
def get_sample_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get available sample categories with counts.
    """
    categories = db.query(Sample.category, func.count(Sample.id)).filter(
        Sample.user_id == current_user.id
    ).group_by(Sample.category).all()
    
    return {
        "categories": [
            {"name": category, "count": count}
            for category, count in categories
        ]
    }


@router.get("/samples/tags", response_model=TagsResponse)
def get_sample_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all unique tags used in user's samples with counts.
    """
    # This is a simplified version - in production you might want to use a separate tags table
    samples = db.query(Sample.tags).filter(
        Sample.user_id == current_user.id,
        Sample.tags.isnot(None)
    ).all()
    
    tag_counts = {}
    for sample in samples:
        if sample.tags:
            for tag in sample.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    return TagsResponse(
        tags=[
            {"name": tag, "count": count}
            for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        ]
    )


@router.get("/samples/{sample_id}", response_model=SampleOut)
def get_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific sample by ID.
    """
    sample = db.query(Sample).filter(
        Sample.id == sample_id,
        Sample.user_id == current_user.id
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    return sample


@router.put("/samples/{sample_id}", response_model=SampleOut)
def update_sample(
    sample_id: int,
    sample_update: SampleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a sample's metadata.
    """
    sample = db.query(Sample).filter(
        Sample.id == sample_id,
        Sample.user_id == current_user.id
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    # Update fields
    update_data = sample_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sample, field, value)
    
    db.commit()
    db.refresh(sample)
    
    return sample


@router.delete("/samples/{sample_id}")
def delete_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a sample and its associated file.
    """
    sample = db.query(Sample).filter(
        Sample.id == sample_id,
        Sample.user_id == current_user.id
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    # Delete file from disk
    try:
        file_path = Path(sample.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Warning: Could not delete file {sample.file_path}: {e}")
    
    # Delete from database
    db.delete(sample)
    db.commit()
    
    return {"message": "Sample deleted successfully"}


@router.get("/samples/{sample_id}/stream")
def stream_sample(
    sample_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream a sample's audio file.
    """
    sample = db.query(Sample).filter(
        Sample.id == sample_id,
        Sample.user_id == current_user.id
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    file_path = Path(sample.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sample file not found")
    
    def iter_file():
        with open(file_path, "rb") as file:
            yield from file
    
    return StreamingResponse(
        iter_file(),
        media_type=sample.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={sample.filename}"
        }
    )


@router.get("/samples/{sample_id}/analysis", response_model=SampleAnalysis)
def get_sample_analysis(
    sample_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed analysis of a sample.
    """
    sample = db.query(Sample).filter(
        Sample.id == sample_id,
        Sample.user_id == current_user.id
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    # Re-analyze the sample to get detailed breakdown
    try:
        analysis = sample_analyzer.analyze_sample(sample.file_path)
        
        return SampleAnalysis(
            basic_properties={
                "duration_sec": analysis.get("duration_sec"),
                "sample_rate": analysis.get("sample_rate"),
                "channels": analysis.get("channels"),
                "size": analysis.get("size")
            },
            musical_features={
                "tempo_bpm": analysis.get("tempo_bpm"),
                "key_signature": analysis.get("key_signature"),
                "time_signature": analysis.get("time_signature")
            },
            spectral_features={
                "spectral_centroid": analysis.get("spectral_centroid"),
                "spectral_rolloff": analysis.get("spectral_rolloff"),
                "zero_crossing_rate": analysis.get("zero_crossing_rate"),
                "mfcc_features": analysis.get("mfcc_features")
            },
            rhythmic_features={
                "rhythm_pattern": analysis.get("rhythm_pattern")
            },
            harmonic_features={
                "harmonic_content": analysis.get("harmonic_content")
            },
            perceptual_features={
                "loudness": analysis.get("loudness"),
                "energy": analysis.get("energy"),
                "complexity": analysis.get("complexity"),
                "intensity": analysis.get("intensity")
            },
            classification={
                "category": analysis.get("category"),
                "tags": analysis.get("tags"),
                "mood": analysis.get("mood"),
                "genre": analysis.get("genre")
            },
            analysis_time=0.0  # Could be calculated if needed
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze sample: {str(e)}") 