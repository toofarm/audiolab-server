from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import os

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

    if not os.path.exists(track.file_path):
        raise HTTPException(
            status_code=404, detail="Audio file not found on disk")

    file_size = os.path.getsize(track.file_path)
    chunk_size = 8192  # 8KB chunks

    def iter_file():
        try:
            with open(track.file_path, "rb") as file:
                bytes_read = 0
                while True:
                    chunk = file.read(chunk_size)
                    if not chunk:  # EOF reached
                        break
                    bytes_read += len(chunk)
                    yield chunk

                # Ensure we've read the entire file
                if bytes_read != file_size:
                    print(
                        f"Warning: Expected {file_size} bytes but read {bytes_read} bytes")
        except Exception as e:
            print(f"Error streaming file {track.file_path}: {e}")
            raise

    return StreamingResponse(
        iter_file(),
        media_type=track.content_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Cache-Control": "public, max-age=3600"
        }
    )
