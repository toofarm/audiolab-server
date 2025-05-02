from pydantic import BaseModel
from typing import Optional


class TrackOut(BaseModel):
    id: int
    filename: str
    content_type: str
    duration: Optional[float]
    sample_rate: Optional[int]
    tempo_bpm: Optional[float]
    loudness_rms: Optional[float]
    estimated_key: Optional[str]

    class Config:
        orm_mode = True
