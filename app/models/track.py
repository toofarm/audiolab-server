from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size = Column(Integer, nullable=True)

    duration_sec = Column(Float)
    sample_rate = Column(Integer)
    tempo_bpm = Column(Float)
    loudness_rms = Column(Float)
    estimated_key = Column(String)
    spectrogram_base64 = Column(String, nullable=True)
    waveplot_base64 = Column(String, nullable=True)

    user = relationship("User", back_populates="tracks")
