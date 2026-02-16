"""
Tests for StorageManager.

Tests cover:
- Initialization
- Atomic writes
- Read/write operations
- Session management
- Error handling
- Crash-during-write simulation
"""

import json
import tempfile
from pathlib import Path

import pytest

from clarity.storage import StorageManager


@pytest.fixture
def temp_clarity_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def storage(temp_clarity_dir):
    """Create a StorageManager instance for testing."""
    return StorageManager(clarity_dir=temp_clarity_dir)


def test_init_storage_creates_directory(storage):
    """Test that init_storage creates the clarity directory."""
    storage.init_storage()
    assert storage.clarity_dir.exists()
    assert storage.clarity_dir.is_dir()


def test_init_storage_creates_audio_directory(storage):
    """Test that init_storage creates the audio subdirectory."""
    storage.init_storage()
    assert storage.audio_dir.exists()
    assert storage.audio_dir.is_dir()


def test_init_storage_creates_sessions_file(storage):
    """Test that init_storage creates clarity_sessions.json."""
    storage.init_storage()
    assert storage.sessions_file.exists()
    assert storage.sessions_file.is_file()


def test_init_storage_creates_valid_schema(storage):
    """Test that the initial JSON has the correct schema."""
    storage.init_storage()

    with storage.sessions_file.open("r") as f:
        data = json.load(f)

    assert "user_profile" in data
    assert "sessions" in data
    assert "phase_transitions" in data

    profile = data["user_profile"]
    assert profile["baseline"] is None
    assert profile["current_phase"] == 1
    assert profile["streak"] == 0
    assert profile["total_sessions"] == 0
    assert "created_at" in profile
    assert profile["last_session_date"] is None

    assert data["sessions"] == []
    assert data["phase_transitions"] == []


def test_storage_exists_returns_false_initially(storage):
    """Test that storage_exists returns False before initialization."""
    assert not storage.storage_exists()


def test_storage_exists_returns_true_after_init(storage):
    """Test that storage_exists returns True after initialization."""
    storage.init_storage()
    assert storage.storage_exists()


def test_read_all_returns_full_data(storage):
    """Test that read_all returns the complete data structure."""
    storage.init_storage()
    data = storage.read_all()

    assert isinstance(data, dict)
    assert "user_profile" in data
    assert "sessions" in data
    assert "phase_transitions" in data


def test_read_profile_returns_user_profile(storage):
    """Test that read_profile returns only the user_profile section."""
    storage.init_storage()
    profile = storage.read_profile()

    assert isinstance(profile, dict)
    assert "baseline" in profile
    assert "current_phase" in profile
    assert "streak" in profile


def test_read_sessions_returns_empty_list_initially(storage):
    """Test that read_sessions returns empty list when no sessions exist."""
    storage.init_storage()
    sessions = storage.read_sessions()

    assert isinstance(sessions, list)
    assert len(sessions) == 0


def test_write_profile_updates_profile(storage):
    """Test that write_profile updates the user profile."""
    storage.init_storage()

    new_data = {"current_phase": 2, "streak": 5}
    storage.write_profile(new_data)

    profile = storage.read_profile()
    assert profile["current_phase"] == 2
    assert profile["streak"] == 5
    # Other fields should be preserved
    assert "baseline" in profile
    assert profile["total_sessions"] == 0


def test_write_baseline_stores_metrics(storage):
    """Test that write_baseline stores baseline metrics."""
    storage.init_storage()

    baseline_metrics = {
        "filler_count": 10,
        "wpm": 150,
        "composite_score": 65,
    }
    storage.write_baseline(baseline_metrics)

    profile = storage.read_profile()
    assert profile["baseline"] is not None
    assert "recorded_at" in profile["baseline"]
    assert profile["baseline"]["metrics"] == baseline_metrics


def test_append_session_adds_session(storage):
    """Test that append_session adds a new session."""
    storage.init_storage()

    session_data = {
        "topic": "Test topic",
        "score": 75,
        "transcript": "Test transcript",
    }
    session_id = storage.append_session(session_data)

    assert session_id == "session_001"

    sessions = storage.read_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == "session_001"
    assert sessions[0]["topic"] == "Test topic"
    assert "created_at" in sessions[0]


def test_append_multiple_sessions_increments_id(storage):
    """Test that appending multiple sessions increments the ID."""
    storage.init_storage()

    id1 = storage.append_session({"topic": "First"})
    id2 = storage.append_session({"topic": "Second"})
    id3 = storage.append_session({"topic": "Third"})

    assert id1 == "session_001"
    assert id2 == "session_002"
    assert id3 == "session_003"

    sessions = storage.read_sessions()
    assert len(sessions) == 3


def test_append_session_updates_total_count(storage):
    """Test that append_session updates total_sessions count."""
    storage.init_storage()

    storage.append_session({"topic": "Test"})

    profile = storage.read_profile()
    assert profile["total_sessions"] == 1
    assert profile["last_session_date"] is not None


def test_get_session_retrieves_by_id(storage):
    """Test that get_session retrieves the correct session."""
    storage.init_storage()

    storage.append_session({"topic": "First", "score": 70})
    storage.append_session({"topic": "Second", "score": 80})

    session = storage.get_session("session_001")
    assert session is not None
    assert session["topic"] == "First"
    assert session["score"] == 70


def test_get_session_returns_none_for_missing_id(storage):
    """Test that get_session returns None for non-existent ID."""
    storage.init_storage()

    session = storage.get_session("session_999")
    assert session is None


def test_get_recent_sessions_returns_last_n(storage):
    """Test that get_recent_sessions returns the N most recent sessions."""
    storage.init_storage()

    for i in range(10):
        storage.append_session({"topic": f"Topic {i}", "number": i})

    recent = storage.get_recent_sessions(count=3)
    assert len(recent) == 3
    # Most recent first
    assert recent[0]["number"] == 9
    assert recent[1]["number"] == 8
    assert recent[2]["number"] == 7


def test_get_recent_sessions_handles_fewer_than_requested(storage):
    """Test that get_recent_sessions works when fewer sessions exist."""
    storage.init_storage()

    storage.append_session({"topic": "First"})
    storage.append_session({"topic": "Second"})

    recent = storage.get_recent_sessions(count=5)
    assert len(recent) == 2


def test_record_phase_transition_creates_record(storage):
    """Test that record_phase_transition creates a transition record."""
    storage.init_storage()

    session_id = storage.append_session({"topic": "Test"})

    metrics = {"filler_avg": 3.5, "composite": 75}
    storage.record_phase_transition(
        from_phase=1, to_phase=2, session_id=session_id, metrics_snapshot=metrics
    )

    data = storage.read_all()
    transitions = data["phase_transitions"]

    assert len(transitions) == 1
    assert transitions[0]["from_phase"] == 1
    assert transitions[0]["to_phase"] == 2
    assert transitions[0]["session_id"] == session_id
    assert transitions[0]["metrics_snapshot"] == metrics
    assert "timestamp" in transitions[0]


def test_record_phase_transition_updates_current_phase(storage):
    """Test that phase transition updates current_phase in profile."""
    storage.init_storage()

    session_id = storage.append_session({"topic": "Test"})
    storage.record_phase_transition(
        from_phase=1, to_phase=2, session_id=session_id, metrics_snapshot={}
    )

    profile = storage.read_profile()
    assert profile["current_phase"] == 2


def test_archive_audio_copies_file(storage, temp_clarity_dir):
    """Test that archive_audio copies audio file to archive directory."""
    storage.init_storage()

    # Create a dummy audio file
    source_audio = temp_clarity_dir / "test.webm"
    source_audio.write_text("fake audio data")

    archived_path = storage.archive_audio(source_audio, "session_001")

    assert archived_path.exists()
    assert archived_path.name == "session_001.webm"
    assert archived_path.read_text() == "fake audio data"


def test_archive_audio_raises_if_source_missing(storage):
    """Test that archive_audio raises FileNotFoundError for missing file."""
    storage.init_storage()

    with pytest.raises(FileNotFoundError):
        storage.archive_audio(Path("/nonexistent/file.webm"), "session_001")


def test_backup_storage_creates_backup(storage):
    """Test that backup_storage creates a timestamped backup."""
    storage.init_storage()

    # Add some data
    storage.append_session({"topic": "Test"})

    backup_path = storage.backup_storage()

    assert backup_path.exists()
    assert "clarity_sessions_backup_" in backup_path.name
    assert backup_path.suffix == ".json"

    # Verify backup has same content
    with backup_path.open("r") as f:
        backup_data = json.load(f)
    assert len(backup_data["sessions"]) == 1


def test_atomic_write_prevents_corruption_on_crash(storage, monkeypatch):
    """
    Test that atomic write pattern prevents corruption.

    Simulates a crash during write by raising exception after temp file created.
    """
    storage.init_storage()

    original_data = storage.read_all()

    # Monkey-patch shutil.move to simulate crash
    def crash_move(*args, **kwargs):
        raise OSError("Simulated crash during write")

    import shutil

    monkeypatch.setattr(shutil, "move", crash_move)

    # Attempt write (should fail)
    with pytest.raises(OSError, match="Failed to write"):
        storage.write_profile({"current_phase": 99})

    # Original file should be unchanged
    data_after = storage.read_all()
    assert data_after == original_data
    assert data_after["user_profile"]["current_phase"] == 1

    # Temp file should be cleaned up
    temp_files = list(storage.clarity_dir.glob("*.tmp"))
    assert len(temp_files) == 0


def test_read_all_raises_if_not_initialized(storage):
    """Test that read_all raises FileNotFoundError if storage not initialized."""
    with pytest.raises(FileNotFoundError):
        storage.read_all()


def test_write_profile_raises_if_not_initialized(storage):
    """Test that write_profile raises FileNotFoundError if storage not initialized."""
    with pytest.raises(FileNotFoundError):
        storage.write_profile({"current_phase": 2})


def test_corrupted_json_raises_decode_error(storage):
    """Test that corrupted JSON raises JSONDecodeError."""
    storage.init_storage()

    # Corrupt the JSON file
    storage.sessions_file.write_text("{ invalid json }")

    with pytest.raises(json.JSONDecodeError):
        storage.read_all()
