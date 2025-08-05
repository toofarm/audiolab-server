"""
Service layer for audio diffusion functionality.
This module provides high-level services for generating audio using the audio-diffusion-pytorch library.
"""

import os
import asyncio
import threading
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import uuid
import logging

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.generated_audio import GeneratedAudio
from app.models.sample import Sample
from app.models.project import Project
from app.models.user import User
from app.lib.audio_diffusion import AudioDiffusionGenerator, create_audio_diffusion_generator
# from app.lib.audio.analyze import analyze_audio_file

logger = logging.getLogger(__name__)

class AudioDiffusionService:
    """
    Service class for handling audio diffusion operations.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "cpu"):
        """
        Initialize the audio diffusion service.
        
        Args:
            model_path: Path to a pre-trained model (optional)
            device: Device to run the model on ('cpu' or 'cuda')
        """
        self.device = device
        self.model_path = model_path
        self.generator = None
        self._initialize_generator()
    
    def _initialize_generator(self):
        """
        Initialize the audio diffusion generator.
        """
        try:
            self.generator = create_audio_diffusion_generator(
                model_path=self.model_path,
                device=self.device
            )
            logger.info(f"Audio diffusion generator initialized on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize audio diffusion generator: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize audio diffusion generator: {str(e)}"
            )
    
    async def generate_audio_async(
        self,
        db: Session,
        user: User,
        project_id: int,
        prompt: str,
        source_sample_ids: Optional[List[int]] = None,
        duration_seconds: float = 10.0,
        num_samples: int = 1,
        guidance_scale: float = 3.0,
        num_inference_steps: int = 50,
        seed: Optional[int] = None
    ) -> GeneratedAudio:
        """
        Generate audio asynchronously and save it to the database.
        
        Args:
            db: Database session
            user: Current user
            project_id: Project ID
            prompt: Text prompt for generation
            source_sample_ids: List of sample IDs to use as conditioning
            duration_seconds: Duration of the generated audio in seconds
            num_samples: Number of samples to generate
            guidance_scale: Guidance scale for generation
            num_inference_steps: Number of inference steps
            seed: Random seed for reproducibility
            
        Returns:
            GeneratedAudio object
        """
        # Verify project exists and belongs to user
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == user.id
        ).first()
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create generation record
        generated_audio = GeneratedAudio(
            user_id=user.id,
            project_id=project_id,
            name=f"Generated Audio {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            description=f"AI-generated audio based on prompt: {prompt}",
            generation_model="audio_diffusion_pytorch",
            generation_prompt=prompt,
            source_samples=source_sample_ids,
            generation_settings={
                "duration_seconds": duration_seconds,
                "num_samples": num_samples,
                "guidance_scale": guidance_scale,
                "num_inference_steps": num_inference_steps,
                "seed": seed,
                "device": self.device
            },
            generation_status="pending",
            filename="",
            file_path="",
            content_type="audio/wav"
        )
        
        db.add(generated_audio)
        db.commit()
        db.refresh(generated_audio)
        
        # Start generation in background
        asyncio.create_task(
            self._generate_audio_background(
                db, generated_audio.id, prompt, source_sample_ids,
                duration_seconds, num_samples, guidance_scale,
                num_inference_steps, seed
            )
        )
        
        return generated_audio
    
    async def _generate_audio_background(
        self,
        db: Session,
        generated_audio_id: int,
        prompt: str,
        source_sample_ids: Optional[List[int]],
        duration_seconds: float,
        num_samples: int,
        guidance_scale: float,
        num_inference_steps: int,
        seed: Optional[int]
    ):
        """
        Generate audio in the background and update the database.
        """
        try:
            # Update status to processing
            self._update_generation_status(db, generated_audio_id, "processing")
            
            # Get source sample paths if provided
            sample_paths = []
            if source_sample_ids:
                samples = db.query(Sample).filter(
                    Sample.id.in_(source_sample_ids),
                    Sample.user_id == db.query(GeneratedAudio.user_id).filter(
                        GeneratedAudio.id == generated_audio_id
                    ).scalar()
                ).all()
                
                sample_paths = [sample.file_path for sample in samples if os.path.exists(sample.file_path)]
            
            # Generate audio
            if sample_paths:
                generated_audio_tensors = self.generator.generate_from_samples(
                    sample_paths=sample_paths,
                    prompt=prompt,
                    duration_seconds=duration_seconds,
                    num_samples=num_samples,
                    guidance_scale=guidance_scale,
                    num_inference_steps=num_inference_steps,
                    seed=seed
                )
            else:
                generated_audio_tensors = self.generator.generate_audio(
                    prompt=prompt,
                    duration_seconds=duration_seconds,
                    num_samples=num_samples,
                    guidance_scale=guidance_scale,
                    num_inference_steps=num_inference_steps,
                    seed=seed
                )
            
            # Save the first generated audio (or iterate through all if needed)
            if generated_audio_tensors:
                audio_tensor = generated_audio_tensors[0]
                
                # Create output directory and filename
                output_dir = Path("/tmp/generated_audio")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"generated_{generated_audio_id}_{uuid.uuid4().hex[:8]}.wav"
                output_path = output_dir / filename
                
                # Save audio
                self.generator.save_audio(audio_tensor, str(output_path))
                
                # Analyze the generated audio
                analysis_features = self.generator.analyze_generated_audio(audio_tensor)
                
                # Update the database record
                self._update_generated_audio_complete(
                    db, generated_audio_id, str(output_path), filename, analysis_features
                )
                
                logger.info(f"Audio generation completed for ID {generated_audio_id}")
            else:
                raise Exception("No audio was generated")
                
        except Exception as e:
            logger.error(f"Audio generation failed for ID {generated_audio_id}: {e}")
            self._update_generation_error(db, generated_audio_id, str(e))
    
    def _update_generation_status(self, db: Session, generated_audio_id: int, status: str):
        """
        Update the generation status in the database.
        """
        try:
            generated_audio = db.query(GeneratedAudio).filter(
                GeneratedAudio.id == generated_audio_id
            ).first()
            
            if generated_audio:
                generated_audio.generation_status = status
                generated_audio.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update generation status: {e}")
    
    def _update_generation_error(self, db: Session, generated_audio_id: int, error: str):
        """
        Update the generation error in the database.
        """
        try:
            generated_audio = db.query(GeneratedAudio).filter(
                GeneratedAudio.id == generated_audio_id
            ).first()
            
            if generated_audio:
                generated_audio.generation_status = "failed"
                generated_audio.generation_error = error
                generated_audio.updated_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update generation error: {e}")
    
    def _update_generated_audio_complete(
        self,
        db: Session,
        generated_audio_id: int,
        file_path: str,
        filename: str,
        analysis_features: Dict[str, Any]
    ):
        """
        Update the generated audio record with completion data.
        """
        try:
            generated_audio = db.query(GeneratedAudio).filter(
                GeneratedAudio.id == generated_audio_id
            ).first()
            
            if generated_audio:
                # Update basic file information
                generated_audio.file_path = file_path
                generated_audio.filename = filename
                generated_audio.generation_status = "completed"
                generated_audio.updated_at = datetime.utcnow()
                
                # Update audio properties from analysis
                generated_audio.duration_sec = analysis_features.get('duration_sec')
                generated_audio.tempo_bpm = analysis_features.get('tempo_bpm')
                generated_audio.spectral_centroid = analysis_features.get('spectral_centroid')
                generated_audio.spectral_rolloff = analysis_features.get('spectral_rolloff')
                generated_audio.zero_crossing_rate = analysis_features.get('zero_crossing_rate')
                generated_audio.mfcc_features = analysis_features.get('mfcc_features')
                generated_audio.loudness = analysis_features.get('rms_energy')
                
                # Calculate file size
                if os.path.exists(file_path):
                    generated_audio.size = os.path.getsize(file_path)
                
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update generated audio completion: {e}")
    
    def get_generation_status(self, db: Session, generated_audio_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get the current status of a generation request.
        
        Args:
            db: Database session
            generated_audio_id: Generated audio ID
            user_id: User ID
            
        Returns:
            Dictionary containing generation status
        """
        generated_audio = db.query(GeneratedAudio).filter(
            GeneratedAudio.id == generated_audio_id,
            GeneratedAudio.user_id == user_id
        ).first()
        
        if not generated_audio:
            raise HTTPException(status_code=404, detail="Generated audio not found")
        
        return {
            "id": generated_audio.id,
            "status": generated_audio.generation_status,
            "error": generated_audio.generation_error,
            "created_at": generated_audio.created_at,
            "updated_at": generated_audio.updated_at,
            "filename": generated_audio.filename if generated_audio.generation_status == "completed" else None
        }
    
    def retry_generation(
        self,
        db: Session,
        generated_audio_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Retry a failed generation request.
        
        Args:
            db: Database session
            generated_audio_id: Generated audio ID
            user_id: User ID
            
        Returns:
            Dictionary containing retry status
        """
        generated_audio = db.query(GeneratedAudio).filter(
            GeneratedAudio.id == generated_audio_id,
            GeneratedAudio.user_id == user_id
        ).first()
        
        if not generated_audio:
            raise HTTPException(status_code=404, detail="Generated audio not found")
        
        if generated_audio.generation_status not in ["failed", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail="Can only retry failed or cancelled generations"
            )
        
        # Reset status and error
        generated_audio.generation_status = "pending"
        generated_audio.generation_error = None
        generated_audio.updated_at = datetime.utcnow()
        db.commit()
        
        # Start generation in background
        asyncio.create_task(
            self._generate_audio_background(
                db, generated_audio_id, generated_audio.generation_prompt,
                generated_audio.source_samples,
                generated_audio.generation_settings.get("duration_seconds", 10.0),
                generated_audio.generation_settings.get("num_samples", 1),
                generated_audio.generation_settings.get("guidance_scale", 3.0),
                generated_audio.generation_settings.get("num_inference_steps", 50),
                generated_audio.generation_settings.get("seed")
            )
        )
        
        return {
            "message": "Generation retry initiated",
            "status": "pending"
        }


# Global service instance
audio_diffusion_service = None

def get_audio_diffusion_service() -> AudioDiffusionService:
    """
    Get the global audio diffusion service instance.
    
    Returns:
        AudioDiffusionService instance
    """
    global audio_diffusion_service
    if audio_diffusion_service is None:
        # Initialize with default settings
        # In production, you might want to load these from environment variables
        model_path = os.getenv("AUDIO_DIFFUSION_MODEL_PATH")
        device = os.getenv("AUDIO_DIFFUSION_DEVICE", "cpu")
        audio_diffusion_service = AudioDiffusionService(
            model_path=model_path,
            device=device
        )
    return audio_diffusion_service 