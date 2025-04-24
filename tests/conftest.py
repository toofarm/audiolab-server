# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base, SessionLocal

# Test database (SQLite in-memory or Docker-based PostgreSQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use PostgreSQL if you prefer

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# Create fresh test DB
Base.metadata.create_all(bind=engine)

# Dependency override


def override_session_local():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[SessionLocal] = override_session_local


@pytest.fixture(scope="module")
def client():
    yield TestClient(app)
