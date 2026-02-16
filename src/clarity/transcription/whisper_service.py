"""
Whisper transcription service with word-level timestamps.

Provides .webm → transcript + timestamps functionality for MVP1.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn


@dataclass
class WordTimestamp:
    """Word with timing information."""

    word: str
    start: float  # seconds
    end: float  # seconds


@dataclass
class TranscriptionResult:
    """Complete transcription result with metadata."""

    transcript: str  # Full transcript text
    words: list[WordTimestamp]  # Word-level timestamps
    duration_seconds: float  # Total audio duration
    word_count: int  # Total words transcribed
    language: str  # Detected language
    model_used: str  # Whisper model size used


class WhisperService:
    """
    Transcription service using faster-whisper with word-level timestamps.

    Handles .webm file input and returns structured transcription results.
    """

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
    ):
        """
        Initialize Whisper service.

        Args:
            model_size: Whisper model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Compute precision (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe_file(
        self,
        audio_path: Path,
        language: str = "en",
        show_progress: bool = True,
    ) -> TranscriptionResult:
        """
        Transcribe audio file with word-level timestamps.

        Args:
            audio_path: Path to audio file (.webm, .wav, .mp3, etc.)
            language: Language code (default: en)
            show_progress: Show progress spinner

        Returns:
            TranscriptionResult with transcript and word-level timestamps

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Load model (first run will download model)
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
            ) as progress:
                progress.add_task("Loading Whisper model...", total=None)
                model = self._load_model()
        else:
            model = self._load_model()

        try:
            # Transcribe with word-level timestamps
            if show_progress:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                ) as progress:
                    progress.add_task("Transcribing audio...", total=None)
                    segments, info = model.transcribe(
                        str(audio_path),
                        language=language,
                        word_timestamps=True,
                        vad_filter=True,  # Voice activity detection
                    )
                    segments = list(segments)  # Consume generator
            else:
                segments, info = model.transcribe(
                    str(audio_path),
                    language=language,
                    word_timestamps=True,
                    vad_filter=True,
                )
                segments = list(segments)

            # Extract words with timestamps
            words = []
            transcript_parts = []

            for segment in segments:
                if hasattr(segment, "words") and segment.words:
                    for word_obj in segment.words:
                        # faster-whisper returns words with .word, .start, .end
                        words.append(
                            WordTimestamp(
                                word=word_obj.word.strip(),
                                start=word_obj.start,
                                end=word_obj.end,
                            )
                        )
                # Also collect segment text for full transcript
                transcript_parts.append(segment.text.strip())

            # Build complete transcript
            transcript = " ".join(transcript_parts)

            # Calculate duration
            duration = words[-1].end if words else 0.0

            # Build result
            return TranscriptionResult(
                transcript=transcript,
                words=words,
                duration_seconds=duration,
                word_count=len(words),
                language=info.language,
                model_used=self.model_size,
            )

        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}") from e

    def transcribe_audio_array(
        self,
        audio_data,
        sample_rate: int,
        language: str = "en",
        show_progress: bool = False,
    ) -> TranscriptionResult:
        """
        Transcribe audio from numpy array.

        Converts audio data to temporary WAV file and transcribes it.

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate in Hz
            language: Language code
            show_progress: Show progress spinner

        Returns:
            TranscriptionResult with transcript and timestamps

        Raises:
            RuntimeError: If transcription fails
        """
        import numpy as np
        from pydub import AudioSegment

        # Convert numpy array to AudioSegment
        audio_segment = AudioSegment(
            data=(audio_data * 32767).astype(np.int16).tobytes(),
            sample_width=2,
            frame_rate=sample_rate,
            channels=1,
        )

        # Save to temporary WAV file
        with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
        ) as temp_file:
            temp_path = Path(temp_file.name)
            audio_segment.export(str(temp_path), format="wav")

        try:
            return self.transcribe_file(
                temp_path, language=language, show_progress=show_progress
            )
        finally:
            # Clean up temp file
            temp_path.unlink(missing_ok=True)

    @staticmethod
    def get_available_models() -> list[str]:
        """
        Get list of available Whisper model sizes.

        Returns:
            List of model names
        """
        return ["tiny", "base", "small", "medium", "large"]

    def estimate_model_memory(self) -> str:
        """
        Estimate memory footprint of current model.

        Returns:
            Human-readable memory estimate
        """
        memory_map = {
            "tiny": "~75 MB",
            "base": "~150 MB",
            "small": "~500 MB",
            "medium": "~1.5 GB",
            "large": "~3 GB",
        }
        return memory_map.get(self.model_size, "Unknown")
