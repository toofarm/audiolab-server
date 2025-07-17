from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from app.db.session import Base
from datetime import datetime


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Project settings and metadata
    genre = Column(String(50), nullable=True)  # Target genre for generation
    mood = Column(String(50), nullable=True)   # Target mood
    tempo_bpm = Column(Float, nullable=True)   # Target tempo
    key_signature = Column(String(10), nullable=True)  # Target key
    
    # Generation settings
    generation_model = Column(String(100), nullable=True)  # 'stable_audio', 'other_ai'
    generation_settings = Column(JSON, nullable=True)  # Model-specific settings
    
    # Project status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)  # For sharing projects
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    samples = relationship("Sample", back_populates="project", cascade="all, delete-orphan")
    generated_audio = relationship("GeneratedAudio", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', user_id={self.user_id})>"