import shutil
import uuid
import time
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.api.auth import get_current_user, get_db
from app.models import GeneratedAudio, Project, User
from app.schemas.generated_audio import (
    GeneratedAudioCreate, GeneratedAudioUpdate, GeneratedAudioOut, 
    GeneratedAudioList, GenerationRequest, GenerationResponse
)
from app.lib.services.audio_diffusion_service import get_audio_diffusion_service

router = APIRouter()

# Generated audio upload directory
GENERATED_AUDIO_DIR = Path("/tmp/generated_audio")
GENERATED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/generated-audio", response_model=GenerationResponse)
async def request_generation(
    generation_request: GenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Request generation of new audio using AI models.
    """
    try:
        # Get the audio diffusion service
        audio_service = get_audio_diffusion_service()
        
        # Extract generation settings
        generation_settings = generation_request.generation_settings or {}
        duration_seconds = generation_settings.get("duration_seconds", 10.0)
        num_samples = generation_settings.get("num_samples", 1)
        guidance_scale = generation_settings.get("guidance_scale", 3.0)
        num_inference_steps = generation_settings.get("num_inference_steps", 50)
        seed = generation_settings.get("seed")
        
        # Generate audio using the service
        generated_audio = await audio_service.generate_audio_async(
            db=db,
            user=current_user,
            project_id=generation_request.project_id,
            prompt=generation_request.prompt,
            source_sample_ids=generation_request.source_sample_ids,
            duration_seconds=duration_seconds,
            num_samples=num_samples,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            seed=seed
        )
        
        return GenerationResponse(
            generation_id=generated_audio.id,
            status="pending",
            estimated_completion_time=30.0,  # Example: 30 seconds
            message="Generation request submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate audio generation: {str(e)}"
        )


@router.get("/generated-audio", response_model=GeneratedAudioList)
def get_generated_audio(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    generation_status: Optional[str] = Query(None, description="Filter by generation status"),
    generation_model: Optional[str] = Query(None, description="Filter by generation model"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of user's generated audio with filtering options.
    """
    # Build query
    query = db.query(GeneratedAudio).filter(GeneratedAudio.user_id == current_user.id)
    
    # Apply filters
    if project_id:
        query = query.filter(GeneratedAudio.project_id == project_id)
    
    if generation_status:
        query = query.filter(GeneratedAudio.generation_status == generation_status)
    
    if generation_model:
        query = query.filter(GeneratedAudio.generation_model == generation_model)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                GeneratedAudio.name.ilike(search_term),
                GeneratedAudio.description.ilike(search_term),
                GeneratedAudio.generation_prompt.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    generated_audio = query.offset(offset).limit(per_page).all()
    
    return GeneratedAudioList(
        generated_audio=generated_audio,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/generated-audio/stats")
def get_generation_stats(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about generated audio.
    """
    query = db.query(GeneratedAudio).filter(GeneratedAudio.user_id == current_user.id)
    
    if project_id:
        query = query.filter(GeneratedAudio.project_id == project_id)
    
    # Get status counts
    status_counts = db.query(
        GeneratedAudio.generation_status,
        func.count(GeneratedAudio.id).label('count')
    ).filter(
        GeneratedAudio.user_id == current_user.id
    )
    
    if project_id:
        status_counts = status_counts.filter(GeneratedAudio.project_id == project_id)
    
    status_counts = status_counts.group_by(GeneratedAudio.generation_status).all()
    
    # Get model counts
    model_counts = db.query(
        GeneratedAudio.generation_model,
        func.count(GeneratedAudio.id).label('count')
    ).filter(
        GeneratedAudio.user_id == current_user.id
    )
    
    if project_id:
        model_counts = model_counts.filter(GeneratedAudio.project_id == project_id)
    
    model_counts = model_counts.group_by(GeneratedAudio.generation_model).all()
    
    # Get total duration
    total_duration = db.query(func.sum(GeneratedAudio.duration_sec)).filter(
        GeneratedAudio.user_id == current_user.id,
        GeneratedAudio.generation_status == "completed"
    )
    
    if project_id:
        total_duration = total_duration.filter(GeneratedAudio.project_id == project_id)
    
    total_duration = total_duration.scalar() or 0.0
    
    return {
        "status_counts": {status: count for status, count in status_counts},
        "model_counts": {model: count for model, count in model_counts},
        "total_duration": total_duration,
        "total_generated": query.count()
    }


@router.get("/generated-audio/{generated_id}", response_model=GeneratedAudioOut)
def get_generated_audio_item(
    generated_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific generated audio item by ID.
    """
    generated_audio = db.query(GeneratedAudio).filter(
        GeneratedAudio.id == generated_id,
        GeneratedAudio.user_id == current_user.id
    ).first()
    
    if not generated_audio:
        raise HTTPException(status_code=404, detail="Generated audio not found")
    
    return generated_audio


@router.put("/generated-audio/{generated_id}", response_model=GeneratedAudioOut)
def update_generated_audio(
    generated_id: int,
    generated_audio_update: GeneratedAudioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update generated audio metadata.
    """
    generated_audio = db.query(GeneratedAudio).filter(
        GeneratedAudio.id == generated_id,
        GeneratedAudio.user_id == current_user.id
    ).first()
    
    if not generated_audio:
        raise HTTPException(status_code=404, detail="Generated audio not found")
    
    # Update fields
    update_data = generated_audio_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(generated_audio, field, value)
    
    generated_audio.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(generated_audio)
    
    return generated_audio


@router.delete("/generated-audio/{generated_id}")
def delete_generated_audio(
    generated_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a generated audio item and its associated file.
    """
    generated_audio = db.query(GeneratedAudio).filter(
        GeneratedAudio.id == generated_id,
        GeneratedAudio.user_id == current_user.id
    ).first()
    
    if not generated_audio:
        raise HTTPException(status_code=404, detail="Generated audio not found")
    
    # Delete file from disk
    try:
        file_path = Path(generated_audio.file_path)
        if file_path.exists():
            file_path.unlink()
    except Exception as e:
        print(f"Warning: Could not delete file {generated_audio.file_path}: {e}")
    
    # Delete from database
    db.delete(generated_audio)
    db.commit()
    
    return {"message": "Generated audio deleted successfully"}


@router.get("/generated-audio/stats")
def get_generation_stats(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about generated audio.
    """
    query = db.query(GeneratedAudio).filter(GeneratedAudio.user_id == current_user.id)
    
    if project_id:
        query = query.filter(GeneratedAudio.project_id == project_id)
    
    # Get status counts
    status_counts = db.query(
        GeneratedAudio.generation_status,
        func.count(GeneratedAudio.id).label('count')
    ).filter(
        GeneratedAudio.user_id == current_user.id
    )
    
    if project_id:
        status_counts = status_counts.filter(GeneratedAudio.project_id == project_id)
    
    status_counts = status_counts.group_by(GeneratedAudio.generation_status).all()
    
    # Get model counts
    model_counts = db.query(
        GeneratedAudio.generation_model,
        func.count(GeneratedAudio.id).label('count')
    ).filter(
        GeneratedAudio.user_id == current_user.id
    )
    
    if project_id:
        model_counts = model_counts.filter(GeneratedAudio.project_id == project_id)
    
    model_counts = model_counts.group_by(GeneratedAudio.generation_model).all()
    
    # Get total duration
    total_duration = db.query(func.sum(GeneratedAudio.duration_sec)).filter(
        GeneratedAudio.user_id == current_user.id,
        GeneratedAudio.generation_status == "completed"
    )
    
    if project_id:
        total_duration = total_duration.filter(GeneratedAudio.project_id == project_id)
    
    total_duration = total_duration.scalar() or 0.0
    
    return {
        "status_counts": {status: count for status, count in status_counts},
        "model_counts": {model: count for model, count in model_counts},
        "total_duration": total_duration,
        "total_generated": query.count()
    }


@router.get("/generated-audio/{generated_id}/stream")
def stream_generated_audio(
    generated_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream a generated audio file.
    """
    generated_audio = db.query(GeneratedAudio).filter(
        GeneratedAudio.id == generated_id,
        GeneratedAudio.user_id == current_user.id
    ).first()
    
    if not generated_audio:
        raise HTTPException(status_code=404, detail="Generated audio not found")
    
    if generated_audio.generation_status != "completed":
        raise HTTPException(status_code=400, detail="Audio generation not completed")
    
    file_path = Path(generated_audio.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Generated audio file not found")
    
    def iter_file():
        with open(file_path, "rb") as file:
            yield from file
    
    return StreamingResponse(
        iter_file(),
        media_type=generated_audio.content_type,
        headers={
            "Content-Disposition": f"attachment; filename={generated_audio.filename}"
        }
    )


@router.get("/generated-audio/{generated_id}/status")
def get_generation_status(
    generated_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current status of a generation request.
    """
    try:
        audio_service = get_audio_diffusion_service()
        return audio_service.get_generation_status(db, generated_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get generation status: {str(e)}"
        )


@router.post("/generated-audio/{generated_id}/retry")
def retry_generation(
    generated_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retry a failed generation request.
    """
    try:
        audio_service = get_audio_diffusion_service()
        return audio_service.retry_generation(db, generated_id, current_user.id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retry generation: {str(e)}"
        )


@router.post("/generated-audio/{generated_id}/cancel")
def cancel_generation(
    generated_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending or processing generation request.
    """
    generated_audio = db.query(GeneratedAudio).filter(
        GeneratedAudio.id == generated_id,
        GeneratedAudio.user_id == current_user.id
    ).first()
    
    if not generated_audio:
        raise HTTPException(status_code=404, detail="Generated audio not found")
    
    if generated_audio.generation_status not in ["pending", "processing"]:
        raise HTTPException(status_code=400, detail="Can only cancel pending or processing generations")
    
    # Update status
    generated_audio.generation_status = "cancelled"
    generated_audio.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(generated_audio)
    
    # TODO: Cancel generation request with AI service
    
    return {
        "message": "Generation cancelled successfully",
        "status": "cancelled"
    }


@router.get("/generated-audio/stats")
def get_generation_stats(
    project_id: Optional[int] = Query(None, description="Filter by project"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics about generated audio.
    """
    query = db.query(GeneratedAudio).filter(GeneratedAudio.user_id == current_user.id)
    
    if project_id:
        query = query.filter(GeneratedAudio.project_id == project_id)
    
    # Get status counts
    status_counts = db.query(
        GeneratedAudio.generation_status,
        func.count(GeneratedAudio.id).label('count')
    ).filter(
        GeneratedAudio.user_id == current_user.id
    )
    
    if project_id:
        status_counts = status_counts.filter(GeneratedAudio.project_id == project_id)
    
    status_counts = status_counts.group_by(GeneratedAudio.generation_status).all()
    
    # Get model counts
    model_counts = db.query(
        GeneratedAudio.generation_model,
        func.count(GeneratedAudio.id).label('count')
    ).filter(
        GeneratedAudio.user_id == current_user.id
    )
    
    if project_id:
        model_counts = model_counts.filter(GeneratedAudio.project_id == project_id)
    
    model_counts = model_counts.group_by(GeneratedAudio.generation_model).all()
    
    # Get total duration
    total_duration = db.query(func.sum(GeneratedAudio.duration_sec)).filter(
        GeneratedAudio.user_id == current_user.id,
        GeneratedAudio.generation_status == "completed"
    )
    
    if project_id:
        total_duration = total_duration.filter(GeneratedAudio.project_id == project_id)
    
    total_duration = total_duration.scalar() or 0.0
    
    return {
        "status_counts": {status: count for status, count in status_counts},
        "model_counts": {model: count for model, count in model_counts},
        "total_duration": total_duration,
        "total_generated": query.count()
    } 