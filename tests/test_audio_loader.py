"""Tests for the audio loading module."""

from pathlib import Path

import numpy as np
import pytest

from clarity.audio_loader import AudioLoader, FFmpegNotFoundError, check_ffmpeg


def test_check_ffmpeg():
    """Test that ffmpeg is available (should pass in CI with ffmpeg installed)."""
    # This will raise if ffmpeg is not found
    check_ffmpeg()


def test_audio_loader_init():
    """Test AudioLoader initialization with default and custom sample rates."""
    loader_default = AudioLoader()
    assert loader_default.sample_rate == 16000

    loader_custom = AudioLoader(sample_rate=22050)
    assert loader_custom.sample_rate == 22050


def test_load_sample_fixture():
    """Test loading the sample.webm fixture."""
    loader = AudioLoader(sample_rate=16000)
    fixture_path = Path(__file__).parent / "fixtures" / "sample.webm"

    audio_data, sample_rate = loader.load(fixture_path)

    # Verify return types and shapes
    assert isinstance(audio_data, np.ndarray)
    assert audio_data.dtype == np.float32
    assert audio_data.ndim == 1  # Mono audio
    assert sample_rate == 16000

    # Verify audio data is in valid range [-1.0, 1.0]
    assert audio_data.min() >= -1.0
    assert audio_data.max() <= 1.0

    # Verify we got some audio (not empty)
    assert len(audio_data) > 0

    # Verify duration is reasonable (sample.webm should be a few seconds)
    duration_seconds = len(audio_data) / sample_rate
    assert 0.1 < duration_seconds < 60  # Between 0.1s and 60s


def test_load_nonexistent_file():
    """Test that loading a nonexistent file raises FileNotFoundError."""
    loader = AudioLoader()

    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        loader.load("nonexistent.webm")


def test_get_duration():
    """Test getting audio duration without loading full audio."""
    loader = AudioLoader()
    fixture_path = Path(__file__).parent / "fixtures" / "sample.webm"

    duration = loader.get_duration(fixture_path)

    # Verify duration is a positive float
    assert isinstance(duration, float)
    assert duration > 0

    # Verify it matches the loaded audio duration (within 0.1s tolerance)
    audio_data, sample_rate = loader.load(fixture_path)
    loaded_duration = len(audio_data) / sample_rate
    assert abs(duration - loaded_duration) < 0.1


def test_get_duration_nonexistent_file():
    """Test that getting duration of nonexistent file raises FileNotFoundError."""
    loader = AudioLoader()

    with pytest.raises(FileNotFoundError, match="Audio file not found"):
        loader.get_duration("nonexistent.webm")


def test_ffmpeg_error_message():
    """Test that FFmpegNotFoundError has helpful installation instructions."""
    error = FFmpegNotFoundError()
    message = str(error)

    # Should contain key information
    assert "FFmpeg" in message
    assert "install" in message.lower()
