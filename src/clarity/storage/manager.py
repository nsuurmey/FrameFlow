"""
Storage Manager for Clarity session data.

Manages the ~/.clarity/ directory and clarity_sessions.json file with atomic writes.
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class StorageManager:
    """
    Manages local JSON storage for Clarity sessions and user profile.

    Uses atomic writes (write to temp file, then rename) to prevent corruption.
    Creates ~/.clarity/ directory on first use.
    """

    def __init__(self, clarity_dir: Path | None = None):
        """
        Initialize storage manager.

        Args:
            clarity_dir: Optional custom clarity directory path.
                        Defaults to ~/.clarity/
        """
        if clarity_dir is None:
            self.clarity_dir = Path.home() / ".clarity"
        else:
            self.clarity_dir = Path(clarity_dir)

        self.sessions_file = self.clarity_dir / "clarity_sessions.json"
        self.audio_dir = self.clarity_dir / "audio"

    def init_storage(self) -> None:
        """
        Initialize storage directory and files if they don't exist.

        Creates:
        - ~/.clarity/ directory
        - ~/.clarity/audio/ directory for audio archive
        - clarity_sessions.json with empty schema

        Raises:
            PermissionError: If cannot create directory or write files
            OSError: If disk full or other OS-level error
        """
        try:
            # Create directories
            self.clarity_dir.mkdir(parents=True, exist_ok=True)
            self.audio_dir.mkdir(parents=True, exist_ok=True)

            # Initialize JSON file if it doesn't exist
            if not self.sessions_file.exists():
                initial_data = {
                    "user_profile": {
                        "baseline": None,
                        "current_phase": 1,
                        "streak": 0,
                        "total_sessions": 0,
                        "created_at": datetime.now().isoformat(),
                        "last_session_date": None,
                    },
                    "sessions": [],
                    "phase_transitions": [],
                }
                self._atomic_write(self.sessions_file, initial_data)

        except PermissionError as e:
            raise PermissionError(
                f"Cannot create Clarity directory at {self.clarity_dir}. "
                f"Check permissions. Error: {e}"
            ) from e
        except OSError as e:
            raise OSError(
                f"Error creating storage at {self.clarity_dir}. "
                f"Check disk space and permissions. Error: {e}"
            ) from e

    def _atomic_write(self, file_path: Path, data: dict[str, Any]) -> None:
        """
        Write JSON data atomically using temp file + rename pattern.

        Args:
            file_path: Target file path
            data: Dictionary to write as JSON

        Raises:
            OSError: If write fails
        """
        temp_path = file_path.with_suffix(".tmp")
        try:
            # Write to temp file
            with temp_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Ensure written to disk

            # Atomic rename
            shutil.move(str(temp_path), str(file_path))

        except Exception as e:
            # Clean up temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise OSError(f"Failed to write {file_path}: {e}") from e

    def storage_exists(self) -> bool:
        """
        Check if storage is initialized.

        Returns:
            True if clarity_sessions.json exists
        """
        return self.sessions_file.exists()

    def read_all(self) -> dict[str, Any]:
        """
        Read entire storage JSON.

        Returns:
            Dictionary with user_profile, sessions, phase_transitions

        Raises:
            FileNotFoundError: If storage not initialized
            json.JSONDecodeError: If JSON is corrupted
        """
        if not self.sessions_file.exists():
            raise FileNotFoundError(
                f"Storage not initialized. Run init_storage() first. "
                f"Expected file: {self.sessions_file}"
            )

        try:
            with self.sessions_file.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Corrupted storage file at {self.sessions_file}. "
                f"Consider restoring from backup or reinitializing.",
                e.doc,
                e.pos,
            ) from e

    def read_profile(self) -> dict[str, Any]:
        """
        Read user profile section.

        Returns:
            Dictionary with baseline, current_phase, streak, etc.

        Raises:
            FileNotFoundError: If storage not initialized
        """
        data = self.read_all()
        return data["user_profile"]

    def read_sessions(self) -> list[dict[str, Any]]:
        """
        Read all sessions.

        Returns:
            List of session dictionaries

        Raises:
            FileNotFoundError: If storage not initialized
        """
        data = self.read_all()
        return data["sessions"]

    def write_profile(self, profile: dict[str, Any]) -> None:
        """
        Update user profile section.

        Args:
            profile: New profile data to merge

        Raises:
            FileNotFoundError: If storage not initialized
            OSError: If write fails
        """
        data = self.read_all()
        data["user_profile"].update(profile)
        self._atomic_write(self.sessions_file, data)

    def write_baseline(self, baseline_metrics: dict[str, Any]) -> None:
        """
        Write baseline metrics to user profile.

        Args:
            baseline_metrics: Baseline session metrics

        Raises:
            FileNotFoundError: If storage not initialized
            OSError: If write fails
        """
        data = self.read_all()
        data["user_profile"]["baseline"] = {
            "recorded_at": datetime.now().isoformat(),
            "metrics": baseline_metrics,
        }
        self._atomic_write(self.sessions_file, data)

    def append_session(self, session: dict[str, Any]) -> str:
        """
        Append a new session to storage.

        Automatically assigns session ID and updates total_sessions count.

        Args:
            session: Session data dictionary

        Returns:
            Session ID (e.g., "session_001")

        Raises:
            FileNotFoundError: If storage not initialized
            OSError: If write fails
        """
        data = self.read_all()

        # Generate session ID
        session_num = len(data["sessions"]) + 1
        session_id = f"session_{session_num:03d}"

        # Add metadata
        session["id"] = session_id
        session["created_at"] = datetime.now().isoformat()

        # Append session
        data["sessions"].append(session)

        # Update profile
        data["user_profile"]["total_sessions"] = session_num
        data["user_profile"]["last_session_date"] = session["created_at"]

        self._atomic_write(self.sessions_file, data)

        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """
        Retrieve a specific session by ID.

        Args:
            session_id: Session ID (e.g., "session_001")

        Returns:
            Session dictionary or None if not found

        Raises:
            FileNotFoundError: If storage not initialized
        """
        sessions = self.read_sessions()
        for session in sessions:
            if session.get("id") == session_id:
                return session
        return None

    def get_recent_sessions(self, count: int = 5) -> list[dict[str, Any]]:
        """
        Get the N most recent sessions.

        Args:
            count: Number of sessions to retrieve

        Returns:
            List of recent session dictionaries (most recent first)

        Raises:
            FileNotFoundError: If storage not initialized
        """
        sessions = self.read_sessions()
        return list(reversed(sessions[-count:]))

    def record_phase_transition(
        self,
        from_phase: int,
        to_phase: int,
        session_id: str,
        metrics_snapshot: dict[str, Any],
    ) -> None:
        """
        Record a phase transition event.

        Args:
            from_phase: Starting phase number
            to_phase: Ending phase number
            session_id: Session that triggered transition
            metrics_snapshot: Metrics at time of transition

        Raises:
            FileNotFoundError: If storage not initialized
            OSError: If write fails
        """
        data = self.read_all()

        transition = {
            "from_phase": from_phase,
            "to_phase": to_phase,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "metrics_snapshot": metrics_snapshot,
        }

        data["phase_transitions"].append(transition)

        # Update current phase in profile
        data["user_profile"]["current_phase"] = to_phase

        self._atomic_write(self.sessions_file, data)

    def archive_audio(self, audio_path: Path, session_id: str) -> Path:
        """
        Copy audio file to archive directory.

        Args:
            audio_path: Source audio file path
            session_id: Session ID for naming

        Returns:
            Path to archived audio file

        Raises:
            FileNotFoundError: If source file doesn't exist
            OSError: If copy fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Preserve original extension
        extension = audio_path.suffix
        archived_path = self.audio_dir / f"{session_id}{extension}"

        try:
            shutil.copy2(str(audio_path), str(archived_path))
            return archived_path
        except OSError as e:
            raise OSError(
                f"Failed to archive audio to {archived_path}: {e}"
            ) from e

    def backup_storage(self) -> Path:
        """
        Create a timestamped backup of clarity_sessions.json.

        Returns:
            Path to backup file

        Raises:
            FileNotFoundError: If storage not initialized
            OSError: If backup fails
        """
        if not self.sessions_file.exists():
            raise FileNotFoundError("No storage file to backup")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.clarity_dir / f"clarity_sessions_backup_{timestamp}.json"

        try:
            shutil.copy2(str(self.sessions_file), str(backup_path))
            return backup_path
        except OSError as e:
            raise OSError(f"Failed to create backup: {e}") from e
