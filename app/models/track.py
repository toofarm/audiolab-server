from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.session import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)

    duration = Column(Float)
    sample_rate = Column(Integer)
    tempo_bpm = Column(Float)
    loudness_rms = Column(Float)
    estimated_key = Column(String)

    user = relationship("User", back_populates="tracks")
