import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import io
import base64


def plot_waveform(y, sr):
    """
    Generate a waveplot from the audio signal.
    """
    # Create a new figure
    plt.figure(figsize=(10, 4))

    # Generate the waveplot
    librosa.display.waveshow(y, sr=sr)

    # Set title and labels
    plt.title('Waveplot')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude')
    plt.tight_layout()

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)

    # Encode the plot to base64
    waveplot_base64 = base64.b64encode(buf.read()).decode('utf-8')

    return f"data:image/png;base64,{waveplot_base64}"
