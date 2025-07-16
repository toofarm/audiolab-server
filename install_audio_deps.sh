#!/bin/bash

# Script to install audio processing dependencies

echo "Installing audio processing dependencies..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install pydub
echo "Installing pydub..."
pip install pydub

# Install additional audio codecs (optional but recommended)
echo "Installing additional audio codecs..."

# For macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS - installing audio codecs..."
    brew install ffmpeg
    brew install libav
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux - installing audio codecs..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
    sudo apt-get install -y libavcodec-extra
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "Detected Windows - please install ffmpeg manually:"
    echo "Download from: https://ffmpeg.org/download.html"
fi

echo "Dependencies installed successfully!"
echo ""
echo "To test audio loading, run:"
echo "python test_audio_loading.py /path/to/your/audio/file.wav" 