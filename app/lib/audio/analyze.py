import io
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
from fastapi import File, UploadFile, HTTPException
import base64


async def analyze_audio(file: UploadFile = File(...)):
    """
    Analyze the audio file and return the analysis results.
    """
    # Check if the file is a valid audio file
    if not file.filename.endswith(('.wav', '.mp3', '.flac')):
        raise HTTPException(
            status_code=400, detail="Invalid audio file format")

    # Read the file content
    contents = await file.read()

    # Reset the file pointer for further operations
    file.file.seek(0)

    # Convert bytes to a buffer for librosa
    audio_buffer = io.BytesIO(contents)

    # Load audio file using librosa
    try:
        y, sr = librosa.load(audio_buffer, sr=None, mono=True)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Could not load audio file")

    # Duration
    duration = librosa.get_duration(y=y, sr=sr)

    # Tempo (BPM)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)

    # Loudness (Root Mean Square)
    rms = np.mean(librosa.feature.rms(y=y))

    # Estimate pitch (very rough key estimation via chroma)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    avg_chroma = np.mean(chroma, axis=1)
    key_index = np.argmax(avg_chroma)
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    key_estimate = keys[key_index]

    # Generate a spectrogram (optional)
    S = librosa.feature.melspectrogram(y=y, sr=sr)
    S_dB = librosa.power_to_db(S, ref=np.max)

    # Generate spectrogram plot
    fig, ax = plt.subplots()
    img = librosa.display.specshow(
        S_dB, sr=sr, x_axis='time', y_axis='mel', ax=ax)
    ax.set(title='Mel-frequency spectrogram')
    plt.colorbar(img, format='%+2.0f dB', ax=ax)

    # Convert plot to base64 string
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close(fig)
    buf.seek(0)
    spectrogram_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return {
        "filename": file.filename,
        "format": file.content_type,
        "duration_sec": round(duration, 2),
        "sample_rate": sr,
        "tempo_bpm": round(float(tempo), 2),
        "loudness_rms": round(float(rms), 5),
        "estimated_key": key_estimate,
        "spectrogram_base64": spectrogram_base64
    }
