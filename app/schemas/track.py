from pydantic import BaseModel
from typing import Optional


class TrackOut(BaseModel):
    id: int
    filename: str
    content_type: str
    size: Optional[int]
    duration_sec: Optional[float]
    sample_rate: Optional[int]
    tempo_bpm: Optional[float]
    loudness_rms: Optional[float]
    estimated_key: Optional[str]
    spectrogram_base64: Optional[str]
    waveplot_base64: Optional[str]

    class Config:
        orm_mode = True
