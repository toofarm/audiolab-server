# backend/tests/conftest.py
import pytest
import hashlib
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.session import Base
from app.api.auth import get_db
from app.models.user import User
from app.core.security import get_password_hash

# Test database (SQLite in-memory or Docker-based PostgreSQL)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use PostgreSQL if you prefer

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)

# 🧹 Reset the DB schema before running any tests


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Create fresh test DB
Base.metadata.create_all(bind=engine)

# Dependency override


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    yield TestClient(app)


@pytest.fixture
def test_user(db):
    user = db.query(User).filter(User.email == "testuser@example.com").first()
    if user:
        return user
    user = User(
        email="testuser@example.com",
        hashed_password=get_password_hash("testpassword"),
        first_name="Test",
        last_name="User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def token_headers(client, test_user):
    # Log in to get the token
    response = client.post(
        "/auth/login",  # update if your login route differs
        data={"username": test_user.email, "password": "testpassword"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
