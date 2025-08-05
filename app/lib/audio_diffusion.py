"""
Audio diffusion module for generating audio using the audio-diffusion-pytorch library.
This module provides functionality to generate audio based on existing samples and prompts.
"""

import os
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from audio_diffusion_pytorch import DiffusionModel, Sampler, Schedule, VDiffusion, VSampler
import librosa
import soundfile as sf
from datetime import datetime
import uuid

class AudioDiffusionGenerator:
    """
    A class to handle audio generation using the audio-diffusion-pytorch library.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        Initialize the audio diffusion generator.
        
        Args:
            model_path: Path to a pre-trained model (optional)
            device: Device to run the model on ('cpu' or 'cuda')
        """
        self.device = device
        self.model = None
        self.model_path = model_path
        
        # Initialize the model if a path is provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            # Create a default model configuration
            self._create_default_model()
    
    def _create_default_model(self):
        """
        Create a default audio diffusion model configuration.
        """
        self.model = DiffusionModel(
            sample_rate=22050,
            n_fft=2048,
            hop_length=512,
            win_length=2048,
            num_layers=4,
            channels=1,
            patch_size=16,
            dim=64,
            depth=6,
            heads=8,
            dim_head=64,
            mlp_dim=128,
            dropout=0.1,
            emb_dropout=0.1
        ).to(self.device)
    
    def load_model(self, model_path: str):
        """
        Load a pre-trained model from the given path.
        
        Args:
            model_path: Path to the model file
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        # Load the model state
        checkpoint = torch.load(model_path, map_location=self.device)
        
        if self.model is None:
            self._create_default_model()
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.eval()
        self.model_path = model_path
    
    def save_model(self, model_path: str):
        """
        Save the current model to the given path.
        
        Args:
            model_path: Path to save the model
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_config': self.model.config if hasattr(self.model, 'config') else None
        }, model_path)
    
    def preprocess_audio(self, audio_path: str, target_sr: int = 22050) -> torch.Tensor:
        """
        Preprocess audio file for the diffusion model.
        
        Args:
            audio_path: Path to the audio file
            target_sr: Target sample rate
            
        Returns:
            Preprocessed audio tensor
        """
        # Load audio using librosa
        audio, sr = librosa.load(audio_path, sr=target_sr, mono=True)
        
        # Convert to tensor
        audio_tensor = torch.from_numpy(audio).float()
        
        # Normalize audio
        if audio_tensor.abs().max() > 0:
            audio_tensor = audio_tensor / audio_tensor.abs().max()
        
        return audio_tensor.unsqueeze(0)  # Add batch dimension
    
    def generate_audio(
        self,
        prompt: str,
        duration_seconds: float = 10.0,
        num_samples: int = 1,
        guidance_scale: float = 3.0,
        num_inference_steps: int = 50,
        seed: Optional[int] = None
    ) -> List[torch.Tensor]:
        """
        Generate audio using the diffusion model.
        
        Args:
            prompt: Text prompt for generation
            duration_seconds: Duration of the generated audio in seconds
            num_samples: Number of samples to generate
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of inference steps
            seed: Random seed for reproducibility
            
        Returns:
            List of generated audio tensors
        """
        if self.model is None:
            raise ValueError("Model not initialized")
        
        if seed is not None:
            torch.manual_seed(seed)
        
        # Calculate the number of samples based on duration
        sample_rate = 22050  # Default sample rate
        num_samples_audio = int(duration_seconds * sample_rate)
        
        # Generate audio
        with torch.no_grad():
            # Create a simple noise input
            noise = torch.randn(num_samples, num_samples_audio, device=self.device)
            
            # Generate audio using the diffusion model
            generated_audio = self.model.sample(
                noise,
                num_steps=num_inference_steps,
                guidance_scale=guidance_scale
            )
        
        return [generated_audio]
    
    def generate_from_samples(
        self,
        sample_paths: List[str],
        prompt: str,
        duration_seconds: float = 10.0,
        num_samples: int = 1,
        guidance_scale: float = 3.0,
        num_inference_steps: int = 50,
        seed: Optional[int] = None
    ) -> List[torch.Tensor]:
        """
        Generate audio using existing samples as conditioning.
        
        Args:
            sample_paths: List of paths to sample audio files
            prompt: Text prompt for generation
            duration_seconds: Duration of the generated audio in seconds
            num_samples: Number of samples to generate
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of inference steps
            seed: Random seed for reproducibility
            
        Returns:
            List of generated audio tensors
        """
        if self.model is None:
            raise ValueError("Model not initialized")
        
        if seed is not None:
            torch.manual_seed(seed)
        
        # Preprocess sample audio
        sample_tensors = []
        for sample_path in sample_paths:
            if os.path.exists(sample_path):
                sample_tensor = self.preprocess_audio(sample_path)
                sample_tensors.append(sample_tensor)
        
        if not sample_tensors:
            raise ValueError("No valid sample files provided")
        
        # Concatenate samples if multiple
        if len(sample_tensors) > 1:
            # Average the samples or use the first one
            conditioning_audio = torch.mean(torch.stack(sample_tensors), dim=0)
        else:
            conditioning_audio = sample_tensors[0]
        
        # Calculate the number of samples based on duration
        sample_rate = 22050  # Default sample rate
        num_samples_audio = int(duration_seconds * sample_rate)
        
        # Generate audio with conditioning
        with torch.no_grad():
            # Create noise input
            noise = torch.randn(num_samples, num_samples_audio, device=self.device)
            
            # Generate audio using the diffusion model with conditioning
            generated_audio = self.model.sample(
                noise,
                num_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                conditioning=conditioning_audio
            )
        
        return [generated_audio]
    
    def save_audio(self, audio_tensor: torch.Tensor, output_path: str, sample_rate: int = 22050):
        """
        Save generated audio tensor to a file.
        
        Args:
            audio_tensor: Audio tensor to save
            output_path: Path to save the audio file
            sample_rate: Sample rate of the audio
        """
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert tensor to numpy array
        audio_np = audio_tensor.squeeze().cpu().numpy()
        
        # Normalize audio
        if audio_np.max() > 1.0 or audio_np.min() < -1.0:
            audio_np = np.clip(audio_np, -1.0, 1.0)
        
        # Save using soundfile
        sf.write(output_path, audio_np, sample_rate)
    
    def analyze_generated_audio(self, audio_tensor: torch.Tensor, sample_rate: int = 22050) -> Dict[str, Any]:
        """
        Analyze generated audio and extract features.
        
        Args:
            audio_tensor: Generated audio tensor
            sample_rate: Sample rate of the audio
            
        Returns:
            Dictionary containing audio analysis features
        """
        # Convert tensor to numpy array
        audio_np = audio_tensor.squeeze().cpu().numpy()
        
        # Extract features using librosa
        features = {}
        
        # Duration
        features['duration_sec'] = len(audio_np) / sample_rate
        
        # Tempo
        tempo, _ = librosa.beat.beat_track(y=audio_np, sr=sample_rate)
        features['tempo_bpm'] = float(tempo)
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=audio_np, sr=sample_rate)
        features['spectral_centroid'] = float(np.mean(spectral_centroids))
        
        spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_np, sr=sample_rate)
        features['spectral_rolloff'] = float(np.mean(spectral_rolloff))
        
        # Zero crossing rate
        zero_crossing_rate = librosa.feature.zero_crossing_rate(audio_np)
        features['zero_crossing_rate'] = float(np.mean(zero_crossing_rate))
        
        # MFCC features
        mfccs = librosa.feature.mfcc(y=audio_np, sr=sample_rate, n_mfcc=13)
        features['mfcc_features'] = mfccs.mean(axis=1).tolist()
        
        # RMS energy
        rms = librosa.feature.rms(y=audio_np)
        features['rms_energy'] = float(np.mean(rms))
        
        return features


def create_audio_diffusion_generator(
    model_path: Optional[str] = None,
    device: str = "cpu"
) -> AudioDiffusionGenerator:
    """
    Factory function to create an AudioDiffusionGenerator instance.
    
    Args:
        model_path: Path to a pre-trained model (optional)
        device: Device to run the model on ('cpu' or 'cuda')
        
    Returns:
        AudioDiffusionGenerator instance
    """
    return AudioDiffusionGenerator(model_path=model_path, device=device) 