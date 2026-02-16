"""
Tests for ConfigManager.

Tests cover:
- Initialization
- Read/write operations
- API key management (env var and config file)
- Whisper model settings
- Audio archive settings
- Validation
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from clarity.config import ConfigManager


@pytest.fixture
def temp_clarity_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config(temp_clarity_dir):
    """Create a ConfigManager instance for testing."""
    return ConfigManager(clarity_dir=temp_clarity_dir)


def test_init_config_creates_file(config):
    """Test that init_config creates config.json."""
    config.init_config()
    assert config.config_file.exists()


def test_init_config_creates_default_values(config):
    """Test that init_config creates file with default values."""
    config.init_config()

    with config.config_file.open("r") as f:
        data = json.load(f)

    assert data["whisper_model"] == "base"
    assert data["archive_audio"] is True
    assert data["anthropic_api_key"] is None


def test_init_config_does_not_overwrite_existing(config):
    """Test that init_config doesn't overwrite existing config."""
    config.init_config()

    # Modify config
    config.set("whisper_model", "large")

    # Try to init again (should not overwrite)
    config.init_config()

    # Value should be preserved
    assert config.get("whisper_model") == "large"


def test_init_config_force_overwrites(config):
    """Test that init_config with force=True overwrites existing config."""
    config.init_config()
    config.set("whisper_model", "large")

    # Force reinit
    config.init_config(force=True)

    # Should be reset to default
    assert config.get("whisper_model") == "base"


def test_config_exists_returns_false_initially(config):
    """Test that config_exists returns False before initialization."""
    assert not config.config_exists()


def test_config_exists_returns_true_after_init(config):
    """Test that config_exists returns True after initialization."""
    config.init_config()
    assert config.config_exists()


def test_read_config_returns_dict(config):
    """Test that read_config returns a dictionary."""
    config.init_config()
    data = config.read_config()

    assert isinstance(data, dict)
    assert "whisper_model" in data
    assert "archive_audio" in data
    assert "anthropic_api_key" in data


def test_read_config_merges_with_defaults(config):
    """Test that read_config merges stored values with defaults."""
    config.init_config()

    # Write partial config (missing some keys)
    with config.config_file.open("w") as f:
        json.dump({"whisper_model": "small"}, f)

    data = config.read_config()

    # Should have merged with defaults
    assert data["whisper_model"] == "small"  # From file
    assert data["archive_audio"] is True  # From defaults
    assert "anthropic_api_key" in data  # From defaults


def test_write_config_saves_file(config):
    """Test that write_config saves configuration."""
    new_config = {
        "whisper_model": "medium",
        "archive_audio": False,
        "anthropic_api_key": "test-key-123",
    }
    config.write_config(new_config)

    # Read back
    data = config.read_config()
    assert data["whisper_model"] == "medium"
    assert data["archive_audio"] is False
    assert data["anthropic_api_key"] == "test-key-123"


def test_get_returns_value(config):
    """Test that get() returns the correct value."""
    config.init_config()
    config.set("whisper_model", "large")

    value = config.get("whisper_model")
    assert value == "large"


def test_get_returns_default_for_missing_key(config):
    """Test that get() returns default for missing key."""
    config.init_config()

    value = config.get("nonexistent_key", "default_value")
    assert value == "default_value"


def test_get_returns_default_if_config_missing(config):
    """Test that get() returns default if config file doesn't exist."""
    # Don't initialize config
    value = config.get("whisper_model", "fallback")
    assert value == "fallback"


def test_set_updates_value(config):
    """Test that set() updates a configuration value."""
    config.init_config()

    config.set("whisper_model", "tiny")

    value = config.get("whisper_model")
    assert value == "tiny"


def test_set_creates_config_if_missing(config):
    """Test that set() creates config file if it doesn't exist."""
    # Don't initialize config
    config.set("whisper_model", "small")

    assert config.config_exists()
    assert config.get("whisper_model") == "small"


def test_get_api_key_from_env_var(config, monkeypatch):
    """Test that get_api_key() prefers environment variable."""
    config.init_config()
    config.set_api_key("config-key-123")

    # Set environment variable
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key-456")

    # Should return env var value, not config file value
    api_key = config.get_api_key()
    assert api_key == "env-key-456"


def test_get_api_key_from_config_file(config):
    """Test that get_api_key() falls back to config file."""
    config.init_config()
    config.set_api_key("config-key-789")

    # No env var set
    api_key = config.get_api_key()
    assert api_key == "config-key-789"


def test_get_api_key_returns_none_if_not_set(config):
    """Test that get_api_key() returns None if key not set."""
    config.init_config()

    api_key = config.get_api_key()
    assert api_key is None


def test_set_api_key_saves_to_config(config):
    """Test that set_api_key() saves key to config file."""
    config.init_config()

    config.set_api_key("my-api-key")

    # Read directly from file
    data = config.read_config()
    assert data["anthropic_api_key"] == "my-api-key"


def test_get_whisper_model_returns_default(config):
    """Test that get_whisper_model() returns default."""
    config.init_config()

    model = config.get_whisper_model()
    assert model == "base"


def test_get_whisper_model_returns_saved_value(config):
    """Test that get_whisper_model() returns saved value."""
    config.init_config()
    config.set_whisper_model("large")

    model = config.get_whisper_model()
    assert model == "large"


def test_set_whisper_model_validates_input(config):
    """Test that set_whisper_model() validates model name."""
    config.init_config()

    with pytest.raises(ValueError, match="Invalid Whisper model"):
        config.set_whisper_model("invalid-model")


def test_set_whisper_model_accepts_valid_models(config):
    """Test that set_whisper_model() accepts all valid model sizes."""
    config.init_config()

    valid_models = ["tiny", "base", "small", "medium", "large"]
    for model in valid_models:
        config.set_whisper_model(model)
        assert config.get_whisper_model() == model


def test_should_archive_audio_returns_default(config):
    """Test that should_archive_audio() returns default (True)."""
    config.init_config()

    should_archive = config.should_archive_audio()
    assert should_archive is True


def test_should_archive_audio_returns_saved_value(config):
    """Test that should_archive_audio() returns saved value."""
    config.init_config()
    config.set_archive_audio(False)

    should_archive = config.should_archive_audio()
    assert should_archive is False


def test_set_archive_audio_updates_config(config):
    """Test that set_archive_audio() updates configuration."""
    config.init_config()

    config.set_archive_audio(False)
    assert config.get("archive_audio") is False

    config.set_archive_audio(True)
    assert config.get("archive_audio") is True


def test_validate_config_warns_about_missing_api_key(config):
    """Test that validate_config() detects missing API key."""
    config.init_config()

    messages = config.validate_config()

    assert "api_key" in messages
    assert "not set" in messages["api_key"]


def test_validate_config_passes_with_api_key_in_config(config):
    """Test that validate_config() passes when API key in config."""
    config.init_config()
    config.set_api_key("valid-key")

    messages = config.validate_config()

    assert "api_key" not in messages


def test_validate_config_passes_with_api_key_in_env(config, monkeypatch):
    """Test that validate_config() passes when API key in env var."""
    config.init_config()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")

    messages = config.validate_config()

    assert "api_key" not in messages


def test_validate_config_detects_invalid_whisper_model(config):
    """Test that validate_config() detects invalid Whisper model."""
    config.init_config()

    # Manually write invalid model (bypassing validation)
    with config.config_file.open("w") as f:
        json.dump({"whisper_model": "invalid"}, f)

    messages = config.validate_config()

    assert "whisper_model" in messages
    assert "Invalid" in messages["whisper_model"]


def test_validate_config_returns_empty_dict_when_valid(config, monkeypatch):
    """Test that validate_config() returns empty dict when all valid."""
    config.init_config()
    config.set_api_key("valid-key")
    config.set_whisper_model("base")

    messages = config.validate_config()

    assert len(messages) == 0


def test_read_config_raises_if_not_initialized(config):
    """Test that read_config() raises FileNotFoundError if not initialized."""
    with pytest.raises(FileNotFoundError):
        config.read_config()


def test_read_config_raises_on_corrupted_json(config):
    """Test that read_config() raises JSONDecodeError on corrupted file."""
    config.init_config()

    # Corrupt the config file
    config.config_file.write_text("{ invalid json }")

    with pytest.raises(json.JSONDecodeError):
        config.read_config()
