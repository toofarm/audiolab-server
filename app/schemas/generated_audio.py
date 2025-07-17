from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class GeneratedAudioBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    generation_prompt: str = Field(..., min_length=1)
    source_samples: Optional[List[int]] = None
    generation_settings: Optional[Dict[str, Any]] = None


class GeneratedAudioCreate(GeneratedAudioBase):
    project_id: int


class GeneratedAudioUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    mood: Optional[str] = None
    genre: Optional[str] = None


class GeneratedAudioOut(GeneratedAudioBase):
    id: int
    user_id: int
    project_id: int
    filename: str
    file_path: str
    content_type: str
    size: Optional[int] = None
    
    # Audio properties
    duration_sec: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: int = 1
    
    # Musical features
    tempo_bpm: Optional[float] = None
    key_signature: Optional[str] = None
    time_signature: Optional[int] = None
    
    # Generation metadata
    generation_model: str
    generation_status: str
    generation_error: Optional[str] = None
    
    # Analysis features
    spectral_centroid: Optional[float] = None
    spectral_rolloff: Optional[float] = None
    zero_crossing_rate: Optional[float] = None
    mfcc_features: Optional[List[List[float]]] = None
    rhythm_pattern: Optional[Dict[str, Any]] = None
    harmonic_content: Optional[Dict[str, Any]] = None
    
    # Perceptual features
    loudness: Optional[float] = None
    energy: Optional[float] = None
    complexity: Optional[float] = None
    intensity: Optional[float] = None
    
    # Classification
    tags: Optional[List[str]] = None
    mood: Optional[str] = None
    genre: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GeneratedAudioList(BaseModel):
    generated_audio: List[GeneratedAudioOut]
    total: int
    page: int
    per_page: int


class GenerationRequest(BaseModel):
    project_id: int
    prompt: str = Field(..., min_length=1)
    source_sample_ids: Optional[List[int]] = None
    generation_settings: Optional[Dict[str, Any]] = None


class GenerationResponse(BaseModel):
    generation_id: int
    status: str
    estimated_completion_time: Optional[float] = None
    message: str