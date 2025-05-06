import librosa
import numpy as np
import pytest

from app.lib.audio.waveplot import plot_waveform
from tests.fixtures import wav_file


# @pytest.mark.asyncio
def test_plot_waveform(wav_file):
    # Load waveform from the BytesIO object using librosa
    # `sr=None` keeps original sample rate
    y, sr = librosa.load(wav_file, sr=None)

    # Call your waveform plotting function
    image_base64 = plot_waveform(y, sr)

    # Check that we got a non-empty base64 string
    assert isinstance(image_base64, str)
    assert len(image_base64) > 1000  # Rough check for PNG size
