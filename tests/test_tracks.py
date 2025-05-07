import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from tests.utils import create_test_track
from tests.fixtures import wav_file


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


def test_get_track_authenticated(client: TestClient, db: Session, test_user: User, token_headers: dict):
    # Create dummy data
    track = create_test_track(db, test_user, filename="song1.wav")

    response = client.get(f"/api/tracks/{track.id}", headers=token_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "song1.wav"
    assert data["id"] == track.id


def test_get_track_not_found(client: TestClient, db: Session, test_user: User, token_headers: dict):
    # Create dummy data
    create_test_track(db, test_user, filename="song1.wav")

    response = client.get("/api/tracks/99999", headers=token_headers)

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Track not found"


def test_get_tracks_unauthenticated(client: TestClient):
    response = client.get("/api/tracks")
    assert response.status_code == 401


def test_upload_audio(client: TestClient, token_headers: dict, wav_file: io.BytesIO):
    # files = {"file": ("test.wav", io.BytesIO(wav_data), "audio/wav")}
    files = {"file": ("test.wav", wav_file, "audio/wav")}

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
    assert "spectrogram_base64" in data
    assert "waveform_base64" in data
