import shutil
import uuid
from pathlib import Path
from sqlalchemy.orm import Session
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.api.auth import get_current_user, get_db
from app.lib.audio.analyze import analyze_audio
from app.models.track import Track

router = APIRouter()

UPLOAD_DIR = Path("/tmp/audio_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    if file.content_type not in ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Save file to temp location with a unique name
    ext = Path(file.filename).suffix
    file_id = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / file_id

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Analyze the audio file
    file.file.seek(0)
    analysis = await analyze_audio(file)

    if not analysis:
        raise HTTPException(
            status_code=400, detail="Failed to analyze audio file")

    track = Track(
        user_id=current_user.id,
        filename=file.filename,
        content_type=file.content_type,
        duration_sec=analysis.get("duration_sec"),
        sample_rate=analysis.get("sample_rate"),
        tempo_bpm=analysis.get("tempo_bpm"),
        loudness_rms=analysis.get("loudness_rms"),
        estimated_key=analysis.get("estimated_key"),
        spectrogram_base64=analysis.get("spectrogram_base64"),
        waveplot_base64=analysis.get("waveplot_base64"),
        size=analysis.get("size", file.file._file.tell()
                          if hasattr(file.file, '_file') else 0),
        file_path=str(file_path),
        # Spotify-like features
        danceability=analysis.get("danceability"),
        energy=analysis.get("energy"),
        valence=analysis.get("valence"),
        acousticness=analysis.get("acousticness"),
        instrumentalness=analysis.get("instrumentalness"),
        liveness=analysis.get("liveness"),
        speechiness=analysis.get("speechiness"),
        loudness=analysis.get("loudness"),
        key=analysis.get("key"),
        mode=analysis.get("mode"),
        time_signature=analysis.get("time_signature"),
    )

    db.add(track)
    db.commit()
    db.refresh(track)

    # Return path or metadata (for now we just return the filename)
    return track
