import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.utils import create_test_track


def test_get_tracks_authenticated(client: TestClient, db: Session, test_user: User, token_headers: dict):
    # Create dummy data
    create_test_track(db, test_user, filename="song1.wav")
    create_test_track(db, test_user, filename="song2.wav")

    response = client.get("/api/tracks", headers=token_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["filename"] == "song1.wav"
    assert data[1]["filename"] == "song2.wav"


def test_get_tracks_unauthenticated(client: TestClient):
    response = client.get("/api/tracks")
    assert response.status_code == 401


def test_upload_audio(client: TestClient, token_headers: dict):
    # Simulate an in-memory WAV file
    wav_data = (
        b"RIFF$\x00\x00\x00WAVEfmt "  # RIFF/WAVE header
        b"\x10\x00\x00\x00\x01\x00\x01\x00"  # PCM format
        b"\x40\x1f\x00\x00\x80>\x00\x00"  # sample rate & byte rate
        b"\x02\x00\x10\x00"              # block align & bits per sample
        b"data\x00\x00\x00\x00"          # data chunk
    )
    files = {"file": ("test.wav", io.BytesIO(wav_data), "audio/wav")}

    response = client.post("/api/upload", files=files, headers=token_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.wav"
    assert "duration" in data
    assert "tempo_bpm" in data
    assert "estimated_key" in data
    assert "loudness_rms" in data
    assert "sample_rate" in data
    assert "content_type" in data
