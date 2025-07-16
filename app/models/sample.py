from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class Sample(Base):
    __tablename__ = "samples"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # 'musical', 'ambient', 'percussion', 'fx', 'voice'
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=True)
    
    # Audio properties
    duration_sec = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, default=1)  # mono/stereo
    
    # Musical features
    tempo_bpm = Column(Float, nullable=True)
    key_signature = Column(String(10), nullable=True)  # 'C', 'C#', 'D', etc.
    time_signature = Column(Integer, nullable=True)  # 4, 3, 6, etc.
    
    # AI-relevant features
    spectral_centroid = Column(Float, nullable=True)  # Brightness (0-1)
    spectral_rolloff = Column(Float, nullable=True)   # Frequency distribution
    zero_crossing_rate = Column(Float, nullable=True) # Noise vs tonal content
    mfcc_features = Column(JSON, nullable=True)       # Mel-frequency cepstral coefficients
    rhythm_pattern = Column(JSON, nullable=True)      # Beat analysis
    harmonic_content = Column(JSON, nullable=True)    # Harmonic analysis
    
    # Perceptual features
    loudness = Column(Float, nullable=True)  # dB
    energy = Column(Float, nullable=True)    # 0-1 scale
    complexity = Column(Float, nullable=True) # 0-1 scale
    
    # Classification
    tags = Column(JSON, nullable=True)  # ['door', 'wood', 'impact', 'reverb']
    mood = Column(String(50), nullable=True)  # 'dark', 'bright', 'mysterious', 'energetic'
    intensity = Column(Float, nullable=True)  # 0-1 scale
    genre = Column(String(50), nullable=True) # 'electronic', 'acoustic', 'industrial'
    
    # AI generation metadata
    is_generated = Column(Integer, default=0)  # 0 = uploaded, 1 = AI generated
    source_samples = Column(JSON, nullable=True)  # For generated samples
    generation_prompt = Column(Text, nullable=True)  # Original generation prompt
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="samples")
    
    def __repr__(self):
        return f"<Sample(id={self.id}, name='{self.name}', category='{self.category}')>" 