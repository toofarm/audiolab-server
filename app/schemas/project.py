from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.schemas.sample import SampleOut
from app.schemas.generated_audio import GeneratedAudioOut


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    tempo_bpm: Optional[float] = Field(None, ge=0)
    key_signature: Optional[str] = None
    generation_model: Optional[str] = None
    generation_settings: Optional[Dict[str, Any]] = None
    is_public: bool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    genre: Optional[str] = None
    mood: Optional[str] = None
    tempo_bpm: Optional[float] = Field(None, ge=0)
    key_signature: Optional[str] = None
    generation_model: Optional[str] = None
    generation_settings: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None


class ProjectOut(ProjectBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectList(BaseModel):
    projects: List[ProjectOut]
    total: int
    page: int
    per_page: int


class ProjectWithSamples(ProjectOut):
    samples: List["SampleOut"] = []
    generated_audio: List["GeneratedAudioOut"] = []


class ProjectStats(BaseModel):
    total_samples: int
    total_generated: int
    total_duration: float
    avg_tempo: Optional[float] = None
    common_genres: List[str] = []
    common_moods: List[str] = []