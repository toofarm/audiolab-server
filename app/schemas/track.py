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
    file_path: Optional[str]

    # Spotify-like audio features
    danceability: Optional[float]
    energy: Optional[float]
    valence: Optional[float]
    acousticness: Optional[float]
    instrumentalness: Optional[float]
    liveness: Optional[float]
    speechiness: Optional[float]
    loudness: Optional[float]
    key: Optional[str]
    mode: Optional[str]
    time_signature: Optional[int]

    class Config:
        orm_mode = True
