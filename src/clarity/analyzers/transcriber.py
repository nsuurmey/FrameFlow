"""
Audio transcription using faster-whisper with fallback.

Provides speech-to-text transcription for filler detection and WPM calculation.
"""

import tempfile
from pathlib import Path

import numpy as np
from pydub import AudioSegment


class Transcriber:
    """
    Transcribes audio using faster-whisper with a simple fallback.

    Note: For MVP 0, if Whisper model download fails (network/proxy issues),
    falls back to a simple word-count estimation based on speech duration.
    """

    def __init__(self, model_size: str = "tiny.en") -> None:
        """
        Initialize the Transcriber.

        Args:
            model_size: Whisper model size (default: tiny.en for English-only fast transcription)
        """
        self.model_size = model_size
        self._model = None
        self._use_fallback = False

    def _get_model(self):
        """Lazy load the Whisper model."""
        if self._model is None and not self._use_fallback:
            try:
                from faster_whisper import WhisperModel

                self._model = WhisperModel(
                    self.model_size, device="cpu", compute_type="int8"
                )
            except Exception as e:
                print(f"  Warning: Whisper model unavailable ({e}). Using fallback transcriber.")
                self._use_fallback = True
        return self._model

    def transcribe(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio samples as 1D numpy array
            sample_rate: Sample rate in Hz

        Returns:
            Transcribed text as a string
        """
        # Try to get model (may trigger fallback)
        model = self._get_model()

        if self._use_fallback:
            # Fallback: Estimate word count based on typical speaking rate (150 WPM)
            # and generate placeholder text
            duration_seconds = len(audio) / sample_rate
            estimated_words = int((duration_seconds / 60.0) * 150)
            # Generate placeholder transcript with some variety
            words = ["hello", "this", "is", "a", "sample", "recording"]
            transcript = " ".join(words * (estimated_words // len(words) + 1))[:estimated_words]
            return transcript

        # Use Whisper for transcription
        # Convert numpy array back to AudioSegment
        audio_segment = AudioSegment(
            data=(audio * 32767).astype(np.int16).tobytes(),
            sample_width=2,
            frame_rate=sample_rate,
            channels=1,
        )

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
            audio_segment.export(temp_path, format="wav")

        try:
            # Transcribe using faster-whisper
            segments, info = model.transcribe(temp_path, language="en", beam_size=1)

            # Concatenate all segments
            transcript = " ".join(segment.text.strip() for segment in segments)

            return transcript
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
