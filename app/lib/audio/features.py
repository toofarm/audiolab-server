import librosa
import numpy as np
from typing import Dict, Any


def extract_audio_features(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Extract Spotify-like audio features from audio signal.

    Args:
        y: Audio time series
        sr: Sample rate

    Returns:
        Dictionary containing audio features
    """
    features = {}

    # 1. Danceability
    # Based on rhythm strength, tempo stability, and beat regularity
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    beat_strength = np.mean(librosa.feature.rms(y=y)[0])

    # Calculate rhythm strength using spectral centroid
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    rhythm_strength = np.std(spectral_centroids) / np.mean(spectral_centroids)

    # Danceability is a combination of tempo, beat strength, and rhythm regularity
    danceability = min(1.0, (tempo / 120.0) * 0.3 +
                       (beat_strength / 0.1) * 0.4 + rhythm_strength * 0.3)
    features['danceability'] = round(float(danceability), 3)

    # 2. Energy
    # Based on RMS energy and spectral rolloff
    rms = librosa.feature.rms(y=y)[0]
    energy = np.mean(rms)
    features['energy'] = round(float(energy), 3)

    # 3. Valence (Positivity/Happiness)
    # Based on harmonic content and spectral features
    # Higher harmonic content often correlates with "happier" music
    harmonic = librosa.effects.harmonic(y)
    harmonic_ratio = np.mean(harmonic) / np.mean(y)

    # Spectral features for mood detection
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]

    # Valence calculation (simplified)
    valence = min(1.0, harmonic_ratio * 0.4 + (1 - np.mean(spectral_rolloff) / (sr/2)) * 0.3 +
                  (1 - np.mean(spectral_bandwidth) / 2000) * 0.3)
    features['valence'] = round(float(valence), 3)

    # 4. Acousticness
    # Based on spectral features that indicate acoustic vs electronic
    # Lower spectral centroid and higher spectral contrast often indicate acoustic instruments
    spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)
    spectral_contrast_mean = np.mean(spectral_contrast)

    # Acousticness calculation
    acousticness = min(1.0, (1 - np.mean(spectral_centroids) / 2000) * 0.5 +
                       (spectral_contrast_mean / 10) * 0.5)
    features['acousticness'] = round(float(acousticness), 3)

    # 5. Instrumentalness
    # Based on vocal detection (simplified approach)
    # Lower values indicate more vocal content
    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    mfcc_variance = np.var(mfccs, axis=1)

    # Simple heuristic: high variance in MFCCs often indicates instrumental music
    instrumentalness = min(1.0, np.mean(mfcc_variance) / 100)
    features['instrumentalness'] = round(float(instrumentalness), 3)

    # 6. Liveness
    # Based on spectral features that indicate live vs studio recording
    # Live recordings often have more spectral variation
    spectral_flatness = librosa.feature.spectral_flatness(y=y)[0]
    liveness = min(1.0, np.std(spectral_flatness) * 10)
    features['liveness'] = round(float(liveness), 3)

    # 7. Speechiness
    # Based on spectral features that distinguish speech from music
    # Speech typically has lower spectral bandwidth and higher spectral centroid
    speech_ratio = (np.mean(spectral_bandwidth) / 2000) * \
        (np.mean(spectral_centroids) / 2000)
    speechiness = min(1.0, speech_ratio * 2)
    features['speechiness'] = round(float(speechiness), 3)

    # 8. Loudness (RMS-based)
    # Convert RMS to dB scale similar to Spotify
    rms_db = 20 * np.log10(np.mean(rms) + 1e-10)
    features['loudness'] = round(float(rms_db), 1)

    # 9. Tempo (BPM)
    features['tempo'] = round(float(tempo), 1)

    # 10. Key and Mode
    # Chroma-based key detection
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    key_index = np.argmax(np.mean(chroma, axis=1))
    keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    features['key'] = keys[key_index]

    # Mode detection (simplified - major vs minor)
    # This is a very basic implementation
    # Default, could be enhanced with more sophisticated detection
    features['mode'] = 'major'

    # 11. Time Signature
    # Detect time signature from beat patterns
    beat_intervals = np.diff(beats)
    if len(beat_intervals) > 0:
        # Simple heuristic for common time signatures
        avg_interval = np.mean(beat_intervals)
        if avg_interval < 0.5:
            time_signature = 4  # 4/4
        elif avg_interval < 0.75:
            time_signature = 3  # 3/4
        else:
            time_signature = 6  # 6/8
    else:
        time_signature = 4
    features['time_signature'] = int(time_signature)

    return features


def get_feature_descriptions() -> Dict[str, str]:
    """
    Get descriptions of what each audio feature represents.
    """
    return {
        'danceability': 'How suitable a track is for dancing based on tempo, rhythm stability, beat strength, and overall regularity',
        'energy': 'A measure of intensity and activity. Typically, energetic tracks feel fast, loud, and noisy',
        'valence': 'A measure describing the musical positiveness conveyed by a track. Tracks with high valence sound more positive',
        'acousticness': 'A confidence measure from 0.0 to 1.0 of whether the track is acoustic',
        'instrumentalness': 'Predicts whether a track contains no vocals. "Ooh" and "aah" sounds are treated as instrumental',
        'liveness': 'Detects the presence of an audience in the recording. Higher liveness values represent an increased probability that the track was performed live',
        'speechiness': 'Detects the presence of spoken words in a track. The more exclusively speech-like the recording, the closer to 1.0',
        'loudness': 'The overall loudness of a track in decibels (dB)',
        'tempo': 'The overall estimated tempo of a track in beats per minute (BPM)',
        'key': 'The key the track is in. Uses standard Pitch Class notation (0 = C, 1 = C♯/D♭, 2 = D, etc.)',
        'mode': 'Mode indicates the modality (major or minor) of a track',
        'time_signature': 'An estimated time signature. The time signature (meter) is a notational convention to specify how many beats are in each bar'
    }
