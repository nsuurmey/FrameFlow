"""
Audio loading module for .webm files.

This module provides functionality to load .webm audio files and convert them
to numpy arrays suitable for analysis with librosa and other audio processing libraries.
"""

import shutil
import sys
from pathlib import Path

import librosa
import numpy as np
from pydub import AudioSegment


class FFmpegNotFoundError(Exception):
    """Raised when ffmpeg is not found on the system."""

    def __init__(self) -> None:
        """Initialize with OS-specific installation instructions."""
        # Detect OS and provide appropriate installation instructions
        if sys.platform == "darwin":
            install_cmd = "brew install ffmpeg"
        elif sys.platform == "linux":
            install_cmd = (
                "sudo apt-get install ffmpeg  # Debian/Ubuntu\n"
                "sudo yum install ffmpeg      # RHEL/CentOS"
            )
        elif sys.platform == "win32":
            install_cmd = "Download from https://ffmpeg.org/download.html"
        else:
            install_cmd = "See https://ffmpeg.org/download.html"

        message = f"""
FFmpeg is required but not found on your system.

Please install FFmpeg:
{install_cmd}

After installation, restart your terminal and try again.
"""
        super().__init__(message.strip())


def check_ffmpeg() -> None:
    """
    Check if ffmpeg is installed and accessible.

    Raises:
        FFmpegNotFoundError: If ffmpeg is not found in PATH
    """
    if shutil.which("ffmpeg") is None:
        raise FFmpegNotFoundError()


class AudioLoader:
    """
    Loads .webm audio files and converts them to numpy arrays.

    This class handles the conversion pipeline from .webm files (using pydub + ffmpeg)
    to numpy arrays suitable for analysis with librosa.
    """

    def __init__(self, sample_rate: int = 16000) -> None:
        """
        Initialize the AudioLoader.

        Args:
            sample_rate: Target sample rate for loaded audio (default: 16000 Hz).
                        Lower sample rates are sufficient for speech analysis.
        """
        self.sample_rate = sample_rate

    def load(self, file_path: str | Path) -> tuple[np.ndarray, int]:
        """
        Load a .webm audio file and convert to numpy array.

        Args:
            file_path: Path to the .webm audio file

        Returns:
            Tuple of (audio_data, sample_rate) where:
                - audio_data: 1D numpy array of float32 audio samples (mono)
                - sample_rate: Sample rate in Hz (matches self.sample_rate)

        Raises:
            FFmpegNotFoundError: If ffmpeg is not installed
            FileNotFoundError: If the audio file doesn't exist
            ValueError: If the file format is not supported
        """
        # Check ffmpeg is available
        check_ffmpeg()

        # Validate file exists
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Load with pydub (uses ffmpeg under the hood)
        try:
            audio = AudioSegment.from_file(str(path))
        except Exception as e:
            raise ValueError(f"Failed to load audio file {file_path}: {e}") from e

        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)

        # Export to numpy array via librosa
        # We use a temporary in-memory buffer
        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

        # Normalize to [-1.0, 1.0] range
        # pydub uses int16 by default, so divide by 32768.0
        if audio.sample_width == 2:  # 16-bit
            samples = samples / 32768.0
        elif audio.sample_width == 4:  # 32-bit
            samples = samples / 2147483648.0

        # Resample to target sample rate using librosa
        original_sr = audio.frame_rate
        if original_sr != self.sample_rate:
            samples = librosa.resample(
                samples, orig_sr=original_sr, target_sr=self.sample_rate
            )

        return samples, self.sample_rate

    def get_duration(self, file_path: str | Path) -> float:
        """
        Get the duration of an audio file in seconds without loading the full audio.

        Args:
            file_path: Path to the .webm audio file

        Returns:
            Duration in seconds

        Raises:
            FFmpegNotFoundError: If ffmpeg is not installed
            FileNotFoundError: If the audio file doesn't exist
        """
        check_ffmpeg()

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        audio = AudioSegment.from_file(str(path))
        return len(audio) / 1000.0  # pydub duration is in milliseconds
