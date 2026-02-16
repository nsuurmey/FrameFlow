"""
Configuration Manager for Clarity.

Manages ~/.clarity/config.json with user preferences and API keys.
"""

import json
import os
from pathlib import Path
from typing import Any


class ConfigManager:
    """
    Manages configuration file for Clarity.

    Config file location: ~/.clarity/config.json
    Supports environment variable overrides for API keys.
    """

    DEFAULT_CONFIG = {
        "whisper_model": "base",  # Options: tiny, base, small, medium, large
        "archive_audio": True,  # Whether to save audio files to ~/.clarity/audio/
        "anthropic_api_key": None,  # Claude API key (prefer env var)
    }

    def __init__(self, clarity_dir: Path | None = None):
        """
        Initialize config manager.

        Args:
            clarity_dir: Optional custom clarity directory path.
                        Defaults to ~/.clarity/
        """
        if clarity_dir is None:
            self.clarity_dir = Path.home() / ".clarity"
        else:
            self.clarity_dir = Path(clarity_dir)

        self.config_file = self.clarity_dir / "config.json"

    def init_config(self, force: bool = False) -> None:
        """
        Initialize config file with default values.

        Args:
            force: If True, overwrite existing config file

        Raises:
            OSError: If write fails
        """
        if self.config_file.exists() and not force:
            return  # Config already exists

        # Ensure directory exists
        self.clarity_dir.mkdir(parents=True, exist_ok=True)

        try:
            with self.config_file.open("w", encoding="utf-8") as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=2)
        except OSError as e:
            raise OSError(f"Failed to create config file: {e}") from e

    def config_exists(self) -> bool:
        """
        Check if config file exists.

        Returns:
            True if config.json exists
        """
        return self.config_file.exists()

    def read_config(self) -> dict[str, Any]:
        """
        Read configuration from file.

        Returns:
            Dictionary with configuration values

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is corrupted
        """
        if not self.config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_file}. "
                f"Run init_config() first."
            )

        try:
            with self.config_file.open("r", encoding="utf-8") as f:
                config = json.load(f)

            # Merge with defaults (in case new keys added)
            merged = self.DEFAULT_CONFIG.copy()
            merged.update(config)

            return merged
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Corrupted config file: {self.config_file}",
                e.doc,
                e.pos,
            ) from e

    def write_config(self, config: dict[str, Any]) -> None:
        """
        Write configuration to file.

        Args:
            config: Configuration dictionary to write

        Raises:
            OSError: If write fails
        """
        # Ensure directory exists
        self.clarity_dir.mkdir(parents=True, exist_ok=True)

        try:
            with self.config_file.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except OSError as e:
            raise OSError(f"Failed to write config: {e}") from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        try:
            config = self.read_config()
            return config.get(key, default)
        except FileNotFoundError:
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set

        Raises:
            OSError: If write fails
        """
        # Read existing config or use defaults
        try:
            config = self.read_config()
        except FileNotFoundError:
            config = self.DEFAULT_CONFIG.copy()

        config[key] = value
        self.write_config(config)

    def get_api_key(self) -> str | None:
        """
        Get Anthropic API key.

        Checks (in order):
        1. ANTHROPIC_API_KEY environment variable
        2. config.json anthropic_api_key field

        Returns:
            API key or None if not found
        """
        # First check environment variable
        env_key = os.environ.get("ANTHROPIC_API_KEY")
        if env_key:
            return env_key

        # Fall back to config file
        return self.get("anthropic_api_key")

    def set_api_key(self, api_key: str) -> None:
        """
        Save API key to config file.

        Args:
            api_key: Anthropic API key to save

        Raises:
            OSError: If write fails
        """
        self.set("anthropic_api_key", api_key)

    def get_whisper_model(self) -> str:
        """
        Get Whisper model size.

        Returns:
            Model size (tiny, base, small, medium, large)
        """
        return self.get("whisper_model", "base")

    def set_whisper_model(self, model: str) -> None:
        """
        Set Whisper model size.

        Args:
            model: Model size (tiny, base, small, medium, large)

        Raises:
            ValueError: If invalid model size
            OSError: If write fails
        """
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if model not in valid_models:
            raise ValueError(
                f"Invalid Whisper model: {model}. "
                f"Must be one of: {', '.join(valid_models)}"
            )

        self.set("whisper_model", model)

    def should_archive_audio(self) -> bool:
        """
        Check if audio archival is enabled.

        Returns:
            True if audio should be archived
        """
        return self.get("archive_audio", True)

    def set_archive_audio(self, enabled: bool) -> None:
        """
        Enable or disable audio archival.

        Args:
            enabled: True to enable archival, False to disable

        Raises:
            OSError: If write fails
        """
        self.set("archive_audio", enabled)

    def validate_config(self) -> dict[str, str]:
        """
        Validate configuration and return any warnings or errors.

        Returns:
            Dictionary with validation messages (empty if all valid)
        """
        messages = {}

        # Check if API key is set
        if not self.get_api_key():
            messages["api_key"] = (
                "Anthropic API key not set. "
                "Set ANTHROPIC_API_KEY environment variable "
                "or run first-time setup."
            )

        # Check Whisper model
        model = self.get_whisper_model()
        valid_models = ["tiny", "base", "small", "medium", "large"]
        if model not in valid_models:
            messages["whisper_model"] = (
                f"Invalid Whisper model '{model}'. "
                f"Must be one of: {', '.join(valid_models)}"
            )

        return messages
