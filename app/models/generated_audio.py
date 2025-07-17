from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class GeneratedAudio(Base):
    __tablename__ = "generated_audio"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Basic metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # File information
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    size = Column(Integer, nullable=True)
    
    # Audio properties (similar to Sample)
    duration_sec = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, default=1)
    
    # Musical features
    tempo_bpm = Column(Float, nullable=True)
    key_signature = Column(String(10), nullable=True)
    time_signature = Column(Integer, nullable=True)
    
    # Generation metadata
    generation_model = Column(String(100), nullable=False)  # 'stable_audio', etc.
    generation_prompt = Column(Text, nullable=False)  # The text prompt used for generation
    source_samples = Column(JSON, nullable=True)  # IDs of samples used as input
    generation_settings = Column(JSON, nullable=True)  # Model-specific settings
    generation_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    generation_error = Column(Text, nullable=True)
    
    # AI analysis features (similar to Sample)
    spectral_centroid = Column(Float, nullable=True)
    spectral_rolloff = Column(Float, nullable=True)
    zero_crossing_rate = Column(Float, nullable=True)
    mfcc_features = Column(JSON, nullable=True)
    rhythm_pattern = Column(JSON, nullable=True)
    harmonic_content = Column(JSON, nullable=True)
    
    # Perceptual features
    loudness = Column(Float, nullable=True)
    energy = Column(Float, nullable=True)
    complexity = Column(Float, nullable=True)
    intensity = Column(Float, nullable=True)
    
    # Classification
    tags = Column(JSON, nullable=True)
    mood = Column(String(50), nullable=True)
    genre = Column(String(50), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="generated_audio")
    project = relationship("Project", back_populates="generated_audio")
    
    def __repr__(self):
        return f"<GeneratedAudio(id={self.id}, name='{self.name}', project_id={self.project_id})>"