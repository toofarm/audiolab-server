from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SampleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: str = Field(..., pattern="^(musical|ambient|percussion|fx|voice)$")
    tags: Optional[List[str]] = None
    mood: Optional[str] = None
    genre: Optional[str] = None


class SampleCreate(SampleBase):
    project_id: Optional[int] = None


class SampleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(musical|ambient|percussion|fx|voice)$")
    tags: Optional[List[str]] = None
    mood: Optional[str] = None
    genre: Optional[str] = None
    project_id: Optional[int] = None


class SampleOut(SampleBase):
    id: int
    user_id: int
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
    
    # AI-relevant features
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
    
    # AI generation metadata
    is_generated: int = 0
    source_samples: Optional[List[int]] = None
    generation_prompt: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Project
    project_id: Optional[int] = None
    
    class Config:
        from_attributes = True


class SampleList(BaseModel):
    samples: List[SampleOut]
    total: int
    page: int
    per_page: int


class SampleFilter(BaseModel):
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    mood: Optional[str] = None
    genre: Optional[str] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    min_tempo: Optional[float] = None
    max_tempo: Optional[float] = None
    key_signature: Optional[str] = None
    min_energy: Optional[float] = None
    max_energy: Optional[float] = None
    min_intensity: Optional[float] = None
    max_intensity: Optional[float] = None
    is_generated: Optional[bool] = None
    search: Optional[str] = None


class SampleUploadResponse(BaseModel):
    sample: SampleOut
    analysis_time: float
    message: str


class SampleAnalysis(BaseModel):
    """Detailed analysis results for a sample"""
    basic_properties: Dict[str, Any]
    musical_features: Dict[str, Any]
    spectral_features: Dict[str, Any]
    rhythmic_features: Dict[str, Any]
    harmonic_features: Dict[str, Any]
    perceptual_features: Dict[str, Any]
    classification: Dict[str, Any]
    analysis_time: float


class CategoryCount(BaseModel):
    """Category with count for filtering"""
    name: str
    count: int


class TagCount(BaseModel):
    """Tag with count for filtering"""
    name: str
    count: int


class CategoriesResponse(BaseModel):
    """Response for categories endpoint"""
    categories: List[CategoryCount]


class TagsResponse(BaseModel):
    """Response for tags endpoint"""
    tags: List[TagCount] 