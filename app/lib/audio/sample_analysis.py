import librosa
import numpy as np
from typing import Dict, Any, List, Tuple
import json
import warnings
import os
from .audio_loader import AudioLoader


class SampleAnalyzer:
    """
    Enhanced audio sample analyzer for AI generation features.
    """
    
    def __init__(self):
        self.sample_rate = 22050  # Standard sample rate for analysis
        self.audio_loader = AudioLoader(self.sample_rate)
        
    def analyze_sample(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Comprehensive analysis of an audio sample.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary containing all extracted features
        """
        # Use the enhanced audio loader
        try:
            y, sr = self.audio_loader.load_audio(audio_file_path)
        except Exception as e:
            raise ValueError(f"Failed to load audio file: {str(e)}")
        
        if len(y) == 0:
            raise ValueError("Audio file is empty or could not be loaded")
        
        # Extract all features
        features = {}
        
        # Basic audio properties
        features.update(self._extract_basic_properties(y, sr))
        
        # Musical features
        features.update(self._extract_musical_features(y, sr))
        
        # Spectral features
        features.update(self._extract_spectral_features(y, sr))
        
        # Rhythmic features
        features.update(self._extract_rhythmic_features(y, sr))
        
        # Harmonic features
        features.update(self._extract_harmonic_features(y, sr))
        
        # Perceptual features
        features.update(self._extract_perceptual_features(y, sr))
        
        # Classification features
        features.update(self._classify_sample(features))
        
        return features
    
    def validate_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Validate an audio file before analysis.
        
        Args:
            audio_file_path: Path to the audio file
            
        Returns:
            Dictionary with validation results
        """
        return self.audio_loader.validate_audio_file(audio_file_path)
    
    def _extract_basic_properties(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract basic audio properties."""
        return {
            'duration_sec': float(librosa.get_duration(y=y, sr=sr)),
            'sample_rate': sr,
            'channels': 1,  # We load as mono
            'size': len(y) * 2,  # Approximate size in bytes (16-bit)
        }
    
    def _extract_musical_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract musical features like tempo, key, etc."""
        features = {}
        
        # Tempo detection
        try:
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            features['tempo_bpm'] = float(tempo)
        except:
            features['tempo_bpm'] = None
        
        # Key detection
        try:
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            key_index = np.argmax(np.mean(chroma, axis=1))
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            features['key_signature'] = keys[key_index]
        except:
            features['key_signature'] = None
        
        # Time signature estimation
        try:
            if 'tempo_bpm' in features and features['tempo_bpm']:
                # Simple heuristic based on tempo
                tempo = features['tempo_bpm']
                if tempo < 80:
                    features['time_signature'] = 3  # 3/4
                elif tempo < 120:
                    features['time_signature'] = 4  # 4/4
                else:
                    features['time_signature'] = 6  # 6/8
            else:
                features['time_signature'] = 4
        except:
            features['time_signature'] = 4
        
        return features
    
    def _extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract spectral features for AI analysis."""
        features = {}
        
        # Spectral centroid (brightness)
        try:
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid'] = float(np.mean(spectral_centroids))
        except:
            features['spectral_centroid'] = None
        
        # Spectral rolloff
        try:
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
        except:
            features['spectral_rolloff'] = None
        
        # Zero crossing rate (noise vs tonal content)
        try:
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            features['zero_crossing_rate'] = float(np.mean(zero_crossing_rate))
        except:
            features['zero_crossing_rate'] = None
        
        # MFCC features (for timbre analysis)
        try:
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_features'] = mfccs.tolist()
        except:
            features['mfcc_features'] = None
        
        return features
    
    def _extract_rhythmic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract rhythmic patterns and features."""
        features = {}
        
        try:
            # Beat tracking
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Rhythm pattern analysis
            if len(beats) > 1:
                beat_intervals = np.diff(beats)
                rhythm_pattern = {
                    'beat_count': len(beats),
                    'avg_interval': float(np.mean(beat_intervals)),
                    'interval_std': float(np.std(beat_intervals)),
                    'rhythm_regularity': float(1.0 - np.std(beat_intervals) / np.mean(beat_intervals))
                }
            else:
                rhythm_pattern = {
                    'beat_count': len(beats),
                    'avg_interval': None,
                    'interval_std': None,
                    'rhythm_regularity': 0.0
                }
            
            features['rhythm_pattern'] = rhythm_pattern
            
        except:
            features['rhythm_pattern'] = {
                'beat_count': 0,
                'avg_interval': None,
                'interval_std': None,
                'rhythm_regularity': 0.0
            }
        
        return features
    
    def _extract_harmonic_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract harmonic content and analysis."""
        features = {}
        
        try:
            # Harmonic separation
            y_harmonic, y_percussive = librosa.effects.hpss(y)
            
            # Harmonic content analysis
            harmonic_ratio = np.sum(np.abs(y_harmonic)) / (np.sum(np.abs(y_harmonic)) + np.sum(np.abs(y_percussive)))
            
            # Chroma features for harmonic analysis
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            harmonic_content = {
                'harmonic_ratio': float(harmonic_ratio),
                'chroma_profile': chroma_mean.tolist(),
                'harmonic_complexity': float(np.std(chroma_mean))
            }
            
            features['harmonic_content'] = harmonic_content
            
        except:
            features['harmonic_content'] = {
                'harmonic_ratio': 0.5,
                'chroma_profile': [0.0] * 12,
                'harmonic_complexity': 0.0
            }
        
        return features
    
    def _extract_perceptual_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract perceptual features like loudness, energy, complexity."""
        features = {}
        
        # Loudness (RMS-based)
        try:
            rms = librosa.feature.rms(y=y)[0]
            loudness_db = 20 * np.log10(np.mean(rms) + 1e-10)
            features['loudness'] = float(loudness_db)
        except:
            features['loudness'] = -60.0
        
        # Energy
        try:
            energy = np.mean(rms)
            features['energy'] = float(energy)
        except:
            features['energy'] = 0.0
        
        # Complexity (based on spectral features)
        try:
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # Complexity is a combination of spectral variation and zero crossing rate
            complexity = (np.std(spectral_centroids) / np.mean(spectral_centroids)) * 0.5 + \
                        (np.std(spectral_rolloff) / np.mean(spectral_rolloff)) * 0.3 + \
                        np.mean(zero_crossing_rate) * 0.2
            
            features['complexity'] = float(min(1.0, complexity))
        except:
            features['complexity'] = 0.5
        
        return features
    
    def _classify_sample(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the sample based on extracted features."""
        classification = {}
        
        # Determine category based on features
        category = self._determine_category(features)
        classification['category'] = category
        
        # Extract tags based on features
        tags = self._extract_tags(features, category)
        classification['tags'] = tags
        
        # Determine mood
        mood = self._determine_mood(features)
        classification['mood'] = mood
        
        # Calculate intensity
        intensity = self._calculate_intensity(features)
        classification['intensity'] = intensity
        
        # Determine genre
        genre = self._determine_genre(features, category)
        classification['genre'] = genre
        
        return classification
    
    def _determine_category(self, features: Dict[str, Any]) -> str:
        """Determine the sample category."""
        # Use harmonic ratio and zero crossing rate to determine category
        harmonic_ratio = features.get('harmonic_content', {}).get('harmonic_ratio', 0.5)
        zero_crossing_rate = features.get('zero_crossing_rate', 0.1)
        energy = features.get('energy', 0.0)
        
        if harmonic_ratio > 0.7:
            return 'musical'
        elif zero_crossing_rate > 0.15:
            return 'percussion'
        elif energy < 0.01:
            return 'ambient'
        else:
            return 'fx'
    
    def _extract_tags(self, features: Dict[str, Any], category: str) -> List[str]:
        """Extract descriptive tags based on features."""
        tags = []
        
        # Spectral tags
        spectral_centroid = features.get('spectral_centroid', 0.5)
        if spectral_centroid > 0.7:
            tags.append('bright')
        elif spectral_centroid < 0.3:
            tags.append('dark')
        
        # Energy tags
        energy = features.get('energy', 0.0)
        if energy > 0.1:
            tags.append('loud')
        elif energy < 0.01:
            tags.append('quiet')
        
        # Complexity tags
        complexity = features.get('complexity', 0.5)
        if complexity > 0.7:
            tags.append('complex')
        elif complexity < 0.3:
            tags.append('simple')
        
        # Category-specific tags
        if category == 'musical':
            tags.extend(['tonal', 'harmonic'])
        elif category == 'percussion':
            tags.extend(['rhythmic', 'percussive'])
        elif category == 'ambient':
            tags.extend(['atmospheric', 'textural'])
        elif category == 'fx':
            tags.extend(['effect', 'impact'])
        
        return tags
    
    def _determine_mood(self, features: Dict[str, Any]) -> str:
        """Determine the mood of the sample."""
        spectral_centroid = features.get('spectral_centroid', 0.5)
        energy = features.get('energy', 0.0)
        complexity = features.get('complexity', 0.5)
        
        if spectral_centroid > 0.7 and energy > 0.05:
            return 'bright'
        elif spectral_centroid < 0.3 and energy < 0.02:
            return 'dark'
        elif energy > 0.1:
            return 'energetic'
        elif complexity > 0.7:
            return 'mysterious'
        else:
            return 'neutral'
    
    def _calculate_intensity(self, features: Dict[str, Any]) -> float:
        """Calculate the intensity of the sample (0-1)."""
        energy = features.get('energy', 0.0)
        complexity = features.get('complexity', 0.5)
        loudness = features.get('loudness', -60.0)
        
        # Normalize loudness to 0-1 scale
        loudness_norm = max(0, (loudness + 60) / 60)
        
        # Combine factors
        intensity = (energy * 0.4 + complexity * 0.3 + loudness_norm * 0.3)
        return float(min(1.0, intensity))
    
    def _determine_genre(self, features: Dict[str, Any], category: str) -> str:
        """Determine the genre of the sample."""
        if category == 'musical':
            spectral_centroid = features.get('spectral_centroid', 0.5)
            if spectral_centroid > 0.6:
                return 'electronic'
            else:
                return 'acoustic'
        elif category == 'percussion':
            return 'percussion'
        elif category == 'ambient':
            return 'ambient'
        else:
            return 'sound_effect' 