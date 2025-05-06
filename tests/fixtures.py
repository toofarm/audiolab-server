import io
import pytest


@pytest.fixture
def wav_file():
    data = (
        b"RIFF$\x00\x00\x00WAVEfmt "
        b"\x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x40\x1f\x00\x00\x80>\x00\x00"
        b"\x02\x00\x10\x00"
        b"data" +
        (88200).to_bytes(4, byteorder="little") +
        b"\x00" * 88200
    )
    return io.BytesIO(data)
