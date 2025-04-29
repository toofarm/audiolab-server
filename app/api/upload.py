import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.api.auth import get_current_user
from app.lib.analyze_audio import analyze_audio

router = APIRouter()

UPLOAD_DIR = Path("/tmp/audio_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user)
):
    if file.content_type not in ["audio/wav", "audio/x-wav", "audio/mpeg", "audio/mp3"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # Save file to temp location with a unique name
    ext = Path(file.filename).suffix
    file_id = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / file_id

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Analyze the audio file
    file.file.seek(0)
    analysis = await analyze_audio(file)

    if not analysis:
        raise HTTPException(
            status_code=400, detail="Failed to analyze audio file")

    # Return path or metadata (for now we just return the filename)
    return {
        "id": file_id,
        **analysis
    }
