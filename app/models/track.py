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
    file_path = Column(String, nullable=True)

    # Spotify-like audio features
    danceability = Column(Float, nullable=True)
    energy = Column(Float, nullable=True)
    valence = Column(Float, nullable=True)
    acousticness = Column(Float, nullable=True)
    instrumentalness = Column(Float, nullable=True)
    liveness = Column(Float, nullable=True)
    speechiness = Column(Float, nullable=True)
    loudness = Column(Float, nullable=True)
    key = Column(String, nullable=True)
    mode = Column(String, nullable=True)
    time_signature = Column(Integer, nullable=True)

    user = relationship("User", back_populates="tracks")
