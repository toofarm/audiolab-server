"""
Enhanced audio loading utility with better format support and error handling.
"""

import os
import warnings
import numpy as np
from typing import Tuple, Optional, Dict, Any
from pathlib import Path

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class AudioLoader:
    """
    Robust audio loader that can handle various formats and provides fallbacks.
    """
    
    def __init__(self, target_sample_rate: int = 22050):
        self.target_sample_rate = target_sample_rate
        self.supported_formats = ['.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac', '.wma']
        
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        Load audio file with multiple fallback methods.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
            
        Raises:
            ValueError: If audio cannot be loaded
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Validate file format
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported audio format: {file_ext}")
        
        # Try librosa first (most reliable for analysis)
        if LIBROSA_AVAILABLE:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
                    audio, sr = librosa.load(file_path, sr=self.target_sample_rate, mono=True)
                    
                if len(audio) > 0:
                    return audio, sr
            except Exception as e:
                print(f"Librosa failed to load {file_path}: {e}")
        
        # Fallback to pydub if available
        if PYDUB_AVAILABLE:
            try:
                audio, sr = self._load_with_pydub(file_path)
                if len(audio) > 0:
                    return audio, sr
            except Exception as e:
                print(f"Pydub failed to load {file_path}: {e}")
        
        # If all else fails, try librosa with different parameters
        if LIBROSA_AVAILABLE:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
                    # Try without resampling
                    audio, sr = librosa.load(file_path, sr=None, mono=True)
                    # Then resample manually
                    if sr != self.target_sample_rate:
                        audio = librosa.resample(audio, orig_sr=sr, target_sr=self.target_sample_rate)
                        sr = self.target_sample_rate
                    
                if len(audio) > 0:
                    return audio, sr
            except Exception as e:
                print(f"Librosa fallback failed to load {file_path}: {e}")
        
        raise ValueError(f"Could not load audio file {file_path} with any available method")
    
    def _load_with_pydub(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Load audio using pydub as fallback."""
        audio_segment = AudioSegment.from_file(file_path)
        
        # Convert to mono if stereo
        if audio_segment.channels > 1:
            audio_segment = audio_segment.set_channels(1)
        
        # Convert to target sample rate
        if audio_segment.frame_rate != self.target_sample_rate:
            audio_segment = audio_segment.set_frame_rate(self.target_sample_rate)
        
        # Convert to numpy array
        samples = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
        
        # Normalize to [-1, 1] range
        if audio_segment.sample_width == 2:  # 16-bit
            samples = samples / 32768.0
        elif audio_segment.sample_width == 4:  # 32-bit
            samples = samples / 2147483648.0
        else:  # 8-bit
            samples = samples / 128.0
        
        return samples, self.target_sample_rate
    
    def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about an audio file without loading it entirely.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary with audio file information
        """
        info = {
            'file_path': file_path,
            'file_size_bytes': os.path.getsize(file_path),
            'file_size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
            'extension': Path(file_path).suffix.lower(),
            'duration_sec': None,
            'sample_rate': None,
            'channels': None,
            'bit_depth': None
        }
        
        # Try to get duration and basic info with librosa
        if LIBROSA_AVAILABLE:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
                    # Load just a small portion to get info
                    audio, sr = librosa.load(file_path, sr=None, mono=True, duration=1.0)
                    info['sample_rate'] = sr
                    info['channels'] = 1
                    
                    # Get full duration
                    duration = librosa.get_duration(path=file_path)
                    info['duration_sec'] = duration
                    
            except Exception as e:
                print(f"Could not get audio info with librosa: {e}")
        
        # Fallback to pydub for info
        if PYDUB_AVAILABLE and (info['duration_sec'] is None or info['sample_rate'] is None):
            try:
                audio_segment = AudioSegment.from_file(file_path)
                info['duration_sec'] = len(audio_segment) / 1000.0  # Convert from ms
                info['sample_rate'] = audio_segment.frame_rate
                info['channels'] = audio_segment.channels
                info['bit_depth'] = audio_segment.sample_width * 8
            except Exception as e:
                print(f"Could not get audio info with pydub: {e}")
        
        return info
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Comprehensive validation of an audio file.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'info': {},
            'loadable': False
        }
        
        try:
            # Basic file checks
            if not os.path.exists(file_path):
                validation['errors'].append(f"File not found: {file_path}")
                return validation
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                validation['errors'].append("File is empty")
                return validation
            
            # Get file info
            validation['info'] = self.get_audio_info(file_path)
            
            # Check file size
            if file_size > 200 * 1024 * 1024:  # 200MB limit
                validation['warnings'].append("File is very large (>200MB), analysis may be slow")
            
            # Check format
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                validation['errors'].append(f"Unsupported format: {file_ext}")
                return validation
            
            # Try to load a small portion
            try:
                audio, sr = self.load_audio(file_path)
                validation['loadable'] = True
                validation['is_valid'] = True
                
                # Check audio quality
                if len(audio) < 1000:  # Less than ~0.05 seconds at 22050Hz
                    validation['warnings'].append("Audio file is very short")
                
                if np.max(np.abs(audio)) < 0.001:
                    validation['warnings'].append("Audio file appears to be very quiet")
                    
            except Exception as e:
                validation['errors'].append(f"Failed to load audio: {str(e)}")
                
        except Exception as e:
            validation['errors'].append(f"Validation error: {str(e)}")
        
        return validation


# Convenience function
def load_audio_file(file_path: str, target_sample_rate: int = 22050) -> Tuple[np.ndarray, int]:
    """
    Convenience function to load an audio file.
    
    Args:
        file_path: Path to the audio file
        target_sample_rate: Target sample rate (default: 22050)
        
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    loader = AudioLoader(target_sample_rate)
    return loader.load_audio(file_path) 