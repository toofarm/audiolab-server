# app/models/revoked_token.py

from sqlalchemy import Column, Integer, String, DateTime
from app.db.session import Base
from datetime import timezone, datetime


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, index=True)
    expires_at = Column(DateTime, default=datetime.now(timezone.utc))
