#!/usr/bin/env python3
"""
Test script for audio loading and analysis.
Run this script to test audio file loading and identify issues.
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.lib.audio.sample_analysis import SampleAnalyzer

def test_audio_file(file_path: str):
    """Test audio file loading and analysis."""
    print(f"\n{'='*60}")
    print(f"Testing audio file: {file_path}")
    print(f"{'='*60}")
    
    analyzer = SampleAnalyzer()
    
    # First, validate the file
    print("\n1. Validating audio file...")
    validation = analyzer.validate_audio_file(file_path)
    
    print(f"   Valid: {validation['is_valid']}")
    print(f"   File info: {validation['file_info']}")
    
    if validation['errors']:
        print(f"   Errors: {validation['errors']}")
        return False
    
    if validation['warnings']:
        print(f"   Warnings: {validation['warnings']}")
    
    # If validation passes, try full analysis
    if validation['is_valid']:
        print("\n2. Running full analysis...")
        try:
            features = analyzer.analyze_sample(file_path)
            print(f"   ✅ Analysis completed successfully!")
            print(f"   Duration: {features.get('duration_sec', 'N/A')} seconds")
            print(f"   Tempo: {features.get('tempo_bpm', 'N/A')} BPM")
            print(f"   Key: {features.get('key_signature', 'N/A')}")
            print(f"   Category: {features.get('category', 'N/A')}")
            print(f"   Mood: {features.get('mood', 'N/A')}")
            return True
        except Exception as e:
            print(f"   ❌ Analysis failed: {str(e)}")
            return False
    
    return False

def main():
    """Main function to test audio files."""
    if len(sys.argv) < 2:
        print("Usage: python test_audio_loading.py <audio_file_path>")
        print("Example: python test_audio_loading.py /path/to/your/audio.wav")
        return
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    success = test_audio_file(file_path)
    
    if success:
        print(f"\n✅ Audio file processed successfully!")
    else:
        print(f"\n❌ Audio file processing failed!")
        print("\nTroubleshooting tips:")
        print("1. Make sure the file is a supported audio format (WAV, MP3, FLAC, OGG, M4A, AAC)")
        print("2. Check that the file is not corrupted")
        print("3. Try converting the file to WAV format using ffmpeg:")
        print("   ffmpeg -i input.mp3 output.wav")
        print("4. Check file permissions")

if __name__ == "__main__":
    main() 