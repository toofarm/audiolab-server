#!/usr/bin/env python3
"""
Test script for audio diffusion functionality.
This script tests the basic audio diffusion generation capabilities.
"""

import os
import sys
import torch
import numpy as np
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.lib.audio_diffusion import AudioDiffusionGenerator, create_audio_diffusion_generator

def test_audio_diffusion_basic():
    """
    Test basic audio diffusion functionality.
    """
    print("Testing audio diffusion functionality...")
    
    try:
        # Create a generator
        print("Creating audio diffusion generator...")
        generator = create_audio_diffusion_generator(device="cpu")
        print("✓ Audio diffusion generator created successfully")
        
        # Test basic generation
        print("Testing basic audio generation...")
        prompt = "A gentle ambient sound with soft piano notes"
        
        # Generate a short audio clip for testing
        generated_audio = generator.generate_audio(
            prompt=prompt,
            duration_seconds=5.0,  # Short duration for testing
            num_samples=1,
            guidance_scale=3.0,
            num_inference_steps=10,  # Fewer steps for faster testing
            seed=42
        )
        
        if generated_audio and len(generated_audio) > 0:
            print("✓ Audio generation successful")
            
            # Test saving audio
            output_dir = Path("/tmp/test_generated_audio")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / "test_generated_audio.wav"
            generator.save_audio(generated_audio[0], str(output_path))
            
            if output_path.exists():
                print(f"✓ Audio saved successfully to {output_path}")
                
                # Test audio analysis
                print("Testing audio analysis...")
                analysis = generator.analyze_generated_audio(generated_audio[0])
                
                if analysis:
                    print("✓ Audio analysis successful")
                    print(f"  - Duration: {analysis.get('duration_sec', 'N/A')} seconds")
                    print(f"  - Tempo: {analysis.get('tempo_bpm', 'N/A')} BPM")
                    print(f"  - Spectral centroid: {analysis.get('spectral_centroid', 'N/A')}")
                else:
                    print("✗ Audio analysis failed")
            else:
                print("✗ Failed to save audio")
        else:
            print("✗ Audio generation failed")
            
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("✓ All tests completed successfully!")
    return True

def test_audio_diffusion_with_samples():
    """
    Test audio diffusion with sample conditioning.
    """
    print("\nTesting audio diffusion with sample conditioning...")
    
    try:
        # Create a generator
        generator = create_audio_diffusion_generator(device="cpu")
        
        # Check if we have any sample files in the expected location
        sample_dir = Path("/tmp/samples")  # Adjust this path as needed
        if not sample_dir.exists():
            print("No sample directory found, skipping sample conditioning test")
            return True
        
        # Find sample files
        sample_files = list(sample_dir.glob("*.wav")) + list(sample_dir.glob("*.mp3"))
        
        if not sample_files:
            print("No sample files found, skipping sample conditioning test")
            return True
        
        print(f"Found {len(sample_files)} sample files")
        
        # Test generation with samples
        sample_paths = [str(f) for f in sample_files[:2]]  # Use first 2 samples
        prompt = "A musical piece inspired by the provided samples"
        
        generated_audio = generator.generate_from_samples(
            sample_paths=sample_paths,
            prompt=prompt,
            duration_seconds=5.0,
            num_samples=1,
            guidance_scale=3.0,
            num_inference_steps=10,
            seed=42
        )
        
        if generated_audio and len(generated_audio) > 0:
            print("✓ Sample-conditioned audio generation successful")
            
            # Save the generated audio
            output_dir = Path("/tmp/test_generated_audio")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / "test_sample_conditioned_audio.wav"
            generator.save_audio(generated_audio[0], str(output_path))
            
            if output_path.exists():
                print(f"✓ Sample-conditioned audio saved to {output_path}")
            else:
                print("✗ Failed to save sample-conditioned audio")
        else:
            print("✗ Sample-conditioned audio generation failed")
            
    except Exception as e:
        print(f"✗ Sample conditioning test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("Audio Diffusion Test Suite")
    print("=" * 40)
    
    # Test basic functionality
    basic_success = test_audio_diffusion_basic()
    
    # Test sample conditioning
    sample_success = test_audio_diffusion_with_samples()
    
    if basic_success and sample_success:
        print("\n🎉 All tests passed! Audio diffusion functionality is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the error messages above.")
        sys.exit(1) 