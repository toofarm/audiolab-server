# Audio Diffusion Functionality

This document describes the audio diffusion functionality integrated into the music app using the `audio-diffusion-pytorch` library.

## Overview

The audio diffusion functionality allows users to generate new audio content based on:
- Text prompts describing the desired audio
- Existing samples as conditioning input
- Various generation parameters (duration, guidance scale, etc.)

## Architecture

### Core Components

1. **AudioDiffusionGenerator** (`app/lib/audio_diffusion.py`)
   - Core class for audio generation using the audio-diffusion-pytorch library
   - Handles model initialization, audio generation, and analysis
   - Supports both text-to-audio and sample-conditioned generation

2. **AudioDiffusionService** (`app/lib/services/audio_diffusion_service.py`)
   - High-level service layer for integrating with the application
   - Handles database operations, background processing, and error handling
   - Manages generation status updates and file storage

3. **API Integration** (`app/api/generated_audio.py`)
   - REST API endpoints for audio generation requests
   - Status checking, retry functionality, and file streaming

### Data Models

- **GeneratedAudio** model stores generation metadata, settings, and results
- Supports various audio features and analysis results
- Tracks generation status (pending, processing, completed, failed)

## Installation

The audio diffusion functionality requires the following dependencies:

```bash
# Core dependencies (already added to requirements/common.txt)
audio-diffusion-pytorch==0.1.3
torch==2.7.1
torchaudio==2.7.1
einops==0.8.1
a-unet==0.0.16
```

## Configuration

### Environment Variables

- `AUDIO_DIFFUSION_MODEL_PATH`: Path to a pre-trained model (optional)
- `AUDIO_DIFFUSION_DEVICE`: Device to run the model on ('cpu' or 'cuda', default: 'cpu')

### Model Configuration

The default model configuration includes:
- Sample rate: 22050 Hz
- FFT size: 2048
- Hop length: 512
- Window length: 2048
- Channels: 1 (mono)
- Patch size: 16
- Model dimensions: 64
- Depth: 6 layers
- Heads: 8 attention heads

## Usage

### Basic Audio Generation

```python
from app.lib.audio_diffusion import create_audio_diffusion_generator

# Create generator
generator = create_audio_diffusion_generator(device="cpu")

# Generate audio from text prompt
generated_audio = generator.generate_audio(
    prompt="A gentle ambient sound with soft piano notes",
    duration_seconds=10.0,
    num_samples=1,
    guidance_scale=3.0,
    num_inference_steps=50,
    seed=42
)

# Save the generated audio
generator.save_audio(generated_audio[0], "output.wav")
```

### Sample-Conditioned Generation

```python
# Generate audio using existing samples as conditioning
sample_paths = ["sample1.wav", "sample2.wav"]
generated_audio = generator.generate_from_samples(
    sample_paths=sample_paths,
    prompt="A musical piece inspired by the provided samples",
    duration_seconds=10.0,
    num_samples=1,
    guidance_scale=3.0,
    num_inference_steps=50,
    seed=42
)
```

### API Usage

#### Request Generation

```bash
POST /api/generated-audio
{
    "project_id": 1,
    "prompt": "A gentle ambient sound with soft piano notes",
    "source_sample_ids": [1, 2, 3],
    "generation_settings": {
        "duration_seconds": 10.0,
        "num_samples": 1,
        "guidance_scale": 3.0,
        "num_inference_steps": 50,
        "seed": 42
    }
}
```

#### Check Generation Status

```bash
GET /api/generated-audio/{generated_id}/status
```

#### Retry Failed Generation

```bash
POST /api/generated-audio/{generated_id}/retry
```

#### Stream Generated Audio

```bash
GET /api/generated-audio/{generated_id}/stream
```

## Testing

Run the test script to verify the audio diffusion functionality:

```bash
cd server
python test_audio_diffusion.py
```

This will test:
- Basic audio generation from text prompts
- Sample-conditioned generation (if samples are available)
- Audio analysis and feature extraction
- File saving and loading

## File Structure

```
server/
├── app/
│   ├── lib/
│   │   ├── audio_diffusion.py              # Core audio diffusion functionality
│   │   └── services/
│   │       └── audio_diffusion_service.py  # Service layer
│   ├── api/
│   │   └── generated_audio.py              # API endpoints
│   └── models/
│       └── generated_audio.py              # Database model
├── requirements/
│   └── common.txt                          # Dependencies
├── test_audio_diffusion.py                 # Test script
└── AUDIO_DIFFUSION_README.md               # This file
```

## Performance Considerations

### Memory Usage

- Audio generation can be memory-intensive, especially for longer durations
- Consider using smaller model configurations for limited resources
- Monitor memory usage during generation

### Processing Time

- Generation time scales with duration and number of inference steps
- Typical generation times: 10-30 seconds for 10-second audio
- Use fewer inference steps for faster generation (trade-off with quality)

### Storage

- Generated audio files are stored in `/tmp/generated_audio/`
- Consider implementing cleanup strategies for old files
- Monitor disk usage for generated audio storage

## Error Handling

The system includes comprehensive error handling:

- Model initialization failures
- Generation errors (out of memory, invalid parameters)
- File system errors (disk full, permission issues)
- Database errors (connection issues, constraint violations)

Errors are logged and stored in the database for debugging.

## Future Enhancements

1. **Model Fine-tuning**: Support for fine-tuning models on user's samples
2. **Batch Processing**: Generate multiple variations simultaneously
3. **Real-time Generation**: Stream generation progress
4. **Advanced Conditioning**: More sophisticated sample conditioning
5. **Quality Metrics**: Automatic quality assessment of generated audio
6. **Model Selection**: Multiple model options for different use cases

## Troubleshooting

### Common Issues

1. **Out of Memory**: Reduce batch size, duration, or model size
2. **Slow Generation**: Use fewer inference steps or smaller model
3. **Poor Quality**: Increase inference steps or adjust guidance scale
4. **Model Loading**: Check model path and file permissions

### Debug Mode

Enable debug logging by setting the log level:

```python
import logging
logging.getLogger('app.lib.audio_diffusion').setLevel(logging.DEBUG)
```

## Contributing

When contributing to the audio diffusion functionality:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new features
3. Update documentation for API changes
4. Consider performance implications
5. Test with various audio formats and durations 