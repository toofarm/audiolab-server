from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.user import User

class AudioMetadata(Base): 
    __tablename__ = "audio_metadata"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="audio_files")
    duration = Column(Integer, nullable=True)  # Duration in seconds
    sample_rate = Column(Integer, nullable=True)  # Sample rate in Hz
    format = Column(String, nullable=True)  # Audio format (e.g., mp3, wav)
    size = Column(Integer, nullable=True)  # Size in bytes
    # Add any additional metadata fields as needed