from app.models.track import Track


def create_test_track(db, user, **kwargs):
    track = Track(
        filename=kwargs.get("filename", "test.wav"),
        content_type=kwargs.get("content_type", "audio/wav"),
        duration=kwargs.get("duration", 123.45),
        sample_rate=kwargs.get("sample_rate", 44100),
        tempo_bpm=kwargs.get("tempo_bpm", 120.0),
        loudness_rms=kwargs.get("loudness_rms", -12.5),
        estimated_key=kwargs.get("estimated_key", "C"),
        user_id=user.id,
    )
    db.add(track)
    db.commit()
    db.refresh(track)
    return track
