from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.models.track import Track
from app.schemas.track import TrackOut
from app.models.user import User
from app.api.auth import get_current_user, get_db

router = APIRouter()


@router.get("/tracks", response_model=List[TrackOut])
def get_tracks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Track).filter(Track.user_id == current_user.id).all()


@router.get("/tracks/{track_id}", response_model=TrackOut)
def get_track(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    track = db.query(Track).filter(Track.id == track_id,
                                   Track.user_id == current_user.id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track


@router.put("/tracks/{track_id}", response_model=TrackOut)
def update_track(
    track_id: int,
    track: TrackOut,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing_track = db.query(Track).filter(Track.id == track_id,
                                            Track.user_id == current_user.id).first()
    if not existing_track:
        raise HTTPException(status_code=404, detail="Track not found")

    for key, value in track.dict(exclude_unset=True).items():
        setattr(existing_track, key, value)

    db.commit()
    db.refresh(existing_track)
    return existing_track


@router.delete("/tracks/{track_id}", response_model=TrackOut)
def delete_track(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    track = db.query(Track).filter(Track.id == track_id,
                                   Track.user_id == current_user.id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    db.delete(track)
    db.commit()
    return track


@router.get("/tracks/{track_id}/stream")
def stream_track(
    track_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    track = db.query(Track).filter(Track.id == track_id,
                                   Track.user_id == current_user.id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    if not track.file_path:
        raise HTTPException(status_code=404, detail="Track file not found")
    if not track.content_type:
        raise HTTPException(
            status_code=400, detail="Track content type not set")

    def iter_file(file_path: str):
        with open(file_path, "rb") as file:
            while chunk := file.read(8192):
                yield chunk

    return StreamingResponse(iter_file(track.file_path),
                             media_type=track.content_type,
                             headers={"Content-Disposition": f"attachment; filename={track.filename}"})
