from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime

from app.api.auth import get_current_user, get_db
from app.models import Project, Sample, GeneratedAudio, User
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut, ProjectList, 
    ProjectWithSamples, ProjectStats
)

router = APIRouter()


@router.post("/projects", response_model=ProjectOut)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new project.
    """
    db_project = Project(
        user_id=current_user.id,
        name=project.name,
        description=project.description,
        genre=project.genre,
        mood=project.mood,
        tempo_bpm=project.tempo_bpm,
        key_signature=project.key_signature,
        generation_model=project.generation_model,
        generation_settings=project.generation_settings,
        is_public=project.is_public
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    return db_project


@router.get("/projects", response_model=ProjectList)
def get_projects(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    mood: Optional[str] = Query(None, description="Filter by mood"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of user's projects with filtering options.
    """
    # Build query
    query = db.query(Project).filter(Project.user_id == current_user.id)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(Project.is_active == is_active)
    
    if genre:
        query = query.filter(Project.genre == genre)
    
    if mood:
        query = query.filter(Project.mood == mood)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Project.name.ilike(search_term)) |
            (Project.description.ilike(search_term))
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    projects = query.offset(offset).limit(per_page).all()
    
    return ProjectList(
        projects=projects,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific project by ID.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.get("/projects/{project_id}/full", response_model=ProjectWithSamples)
def get_project_with_samples(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a project with its associated samples and generated audio.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get samples for this project
    samples = db.query(Sample).filter(
        Sample.project_id == project_id,
        Sample.user_id == current_user.id
    ).all()
    
    # Get generated audio for this project
    generated_audio = db.query(GeneratedAudio).filter(
        GeneratedAudio.project_id == project_id,
        GeneratedAudio.user_id == current_user.id
    ).all()
    
    # Create response with samples and generated audio
    project_with_samples = ProjectWithSamples(
        **project.__dict__,
        samples=samples,
        generated_audio=generated_audio
    )
    
    return project_with_samples


@router.put("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a project's metadata.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a project and all its associated samples and generated audio.
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete from database (cascade will handle samples and generated audio)
    db.delete(project)
    db.commit()
    
    return {"message": "Project deleted successfully"}


@router.get("/projects/{project_id}/samples")
def get_project_samples(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get samples associated with a specific project.
    """
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get samples for this project
    query = db.query(Sample).filter(
        Sample.project_id == project_id,
        Sample.user_id == current_user.id
    )
    
    total = query.count()
    offset = (page - 1) * per_page
    samples = query.offset(offset).limit(per_page).all()
    
    return {
        "samples": samples,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/projects/{project_id}/generated")
def get_project_generated_audio(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by generation status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get generated audio associated with a specific project.
    """
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get generated audio for this project
    query = db.query(GeneratedAudio).filter(
        GeneratedAudio.project_id == project_id,
        GeneratedAudio.user_id == current_user.id
    )
    
    if status:
        query = query.filter(GeneratedAudio.generation_status == status)
    
    total = query.count()
    offset = (page - 1) * per_page
    generated_audio = query.offset(offset).limit(per_page).all()
    
    return {
        "generated_audio": generated_audio,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/projects/{project_id}/stats", response_model=ProjectStats)
def get_project_stats(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics for a specific project.
    """
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get sample statistics
    sample_stats = db.query(
        func.count(Sample.id).label('total_samples'),
        func.sum(Sample.duration_sec).label('total_duration'),
        func.avg(Sample.tempo_bpm).label('avg_tempo')
    ).filter(
        Sample.project_id == project_id,
        Sample.user_id == current_user.id
    ).first()
    
    # Get generated audio statistics
    generated_stats = db.query(
        func.count(GeneratedAudio.id).label('total_generated')
    ).filter(
        GeneratedAudio.project_id == project_id,
        GeneratedAudio.user_id == current_user.id
    ).first()
    
    # Get common genres and moods from samples
    genres = db.query(Sample.genre).filter(
        Sample.project_id == project_id,
        Sample.user_id == current_user.id,
        Sample.genre.isnot(None)
    ).distinct().all()
    
    moods = db.query(Sample.mood).filter(
        Sample.project_id == project_id,
        Sample.user_id == current_user.id,
        Sample.mood.isnot(None)
    ).distinct().all()
    
    return ProjectStats(
        total_samples=sample_stats.total_samples or 0,
        total_generated=generated_stats.total_generated or 0,
        total_duration=sample_stats.total_duration or 0.0,
        avg_tempo=sample_stats.avg_tempo,
        common_genres=[g.genre for g in genres if g.genre],
        common_moods=[m.mood for m in moods if m.mood]
    )


@router.post("/projects/{project_id}/samples/{sample_id}")
def add_sample_to_project(
    project_id: int,
    sample_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add an existing sample to a project.
    """
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify sample exists and belongs to user
    sample = db.query(Sample).filter(
        Sample.id == sample_id,
        Sample.user_id == current_user.id
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    # Add sample to project
    sample.project_id = project_id
    db.commit()
    db.refresh(sample)
    
    return {"message": "Sample added to project successfully"}


@router.delete("/projects/{project_id}/samples/{sample_id}")
def remove_sample_from_project(
    project_id: int,
    sample_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a sample from a project (doesn't delete the sample).
    """
    # Verify project exists and belongs to user
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify sample exists, belongs to user, and is in this project
    sample = db.query(Sample).filter(
        Sample.id == sample_id,
        Sample.user_id == current_user.id,
        Sample.project_id == project_id
    ).first()
    
    if not sample:
        raise HTTPException(status_code=404, detail="Sample not found in project")
    
    # Remove sample from project
    sample.project_id = None
    db.commit()
    
    return {"message": "Sample removed from project successfully"} 