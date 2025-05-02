from fastapi import APIRouter, Depends
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
