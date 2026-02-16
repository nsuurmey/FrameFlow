"""
First-run setup flow.

Guides user through initial setup:
1. Create ~/.clarity/ directory
2. Initialize storage JSON
3. Create config file
4. Prompt for API key
5. Download Whisper model (with progress bar)
"""

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from clarity.config import ConfigManager
from clarity.storage import StorageManager


class FirstRunSetup:
    """
    Manages first-run setup flow for Clarity.

    Coordinates storage initialization, config creation, and API key setup.
    """

    def __init__(
        self,
        clarity_dir: Path | None = None,
        console: Console | None = None,
    ):
        """
        Initialize first-run setup.

        Args:
            clarity_dir: Optional custom clarity directory path
            console: Optional Rich console instance
        """
        self.clarity_dir = clarity_dir or Path.home() / ".clarity"
        self.console = console or Console()
        self.storage = StorageManager(clarity_dir=clarity_dir)
        self.config = ConfigManager(clarity_dir=clarity_dir)

    def is_first_run(self) -> bool:
        """
        Check if this is the first run.

        Returns:
            True if storage or config doesn't exist
        """
        return not self.storage.storage_exists() or not self.config.config_exists()

    def run_setup(self, skip_api_key: bool = False) -> bool:
        """
        Run the complete first-run setup flow.

        Args:
            skip_api_key: If True, skip API key prompt (for testing)

        Returns:
            True if setup completed successfully

        Raises:
            KeyboardInterrupt: If user cancels setup
        """
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Welcome to Clarity![/bold cyan]\n\n"
            "Let's set up your speaking practice environment.\n\n"
            "This will:\n"
            "  • Create your practice directory (~/.clarity/)\n"
            "  • Initialize session storage\n"
            "  • Configure your preferences\n"
            "  • Set up your Claude API key",
            title="✨ First-Time Setup",
        ))
        self.console.print()

        try:
            # Step 1: Create directory and storage
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Creating storage directory...", total=None)
                self.storage.init_storage()
                progress.update(task, completed=True)

            self.console.print("✓ Storage initialized at:", str(self.clarity_dir))
            self.console.print()

            # Step 2: Initialize config
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                task = progress.add_task("Creating configuration file...", total=None)
                self.config.init_config()
                progress.update(task, completed=True)

            self.console.print("✓ Configuration file created")
            self.console.print()

            # Step 3: API key setup
            if not skip_api_key:
                self._setup_api_key()

            # Step 4: Whisper model selection
            self._setup_whisper_model()

            # Step 5: Audio archive preference
            self._setup_audio_archive()

            # Success message
            self.console.print()
            self.console.print(Panel.fit(
                "[bold green]Setup Complete![/bold green]\n\n"
                "You're ready to start practicing!\n\n"
                "Try these commands:\n"
                "  • [cyan]clarity baseline[/cyan] - Record your baseline\n"
                "  • [cyan]clarity practice[/cyan] - Start a practice session\n"
                "  • [cyan]clarity status[/cyan] - Check your progress",
                title="✅ Ready",
            ))
            self.console.print()

            return True

        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Setup cancelled by user.[/yellow]")
            self.console.print(
                "Run [cyan]clarity[/cyan] again to complete setup.\n"
            )
            raise

        except Exception as e:
            self.console.print(f"\n[red]Setup failed: {e}[/red]")
            return False

    def _setup_api_key(self) -> None:
        """
        Prompt user for API key and save to config.

        Checks environment variable first.
        """
        self.console.print("[bold]Claude API Key Setup[/bold]")
        self.console.print()

        # Check if already set in environment
        env_key = os.environ.get("ANTHROPIC_API_KEY")
        if env_key:
            self.console.print(
                "✓ API key found in ANTHROPIC_API_KEY environment variable"
            )
            self.console.print()
            return

        # Prompt for API key
        self.console.print(
            "You'll need an Anthropic API key to use Claude for analysis."
        )
        self.console.print(
            "Get your API key at: [link]https://console.anthropic.com/[/link]"
        )
        self.console.print()

        while True:
            api_key = Prompt.ask(
                "Enter your Claude API key (or press Enter to skip)",
                password=True,
                default="",
            )

            if not api_key:
                self.console.print(
                    "[yellow]Skipping API key setup. "
                    "You can set it later with ANTHROPIC_API_KEY env var.[/yellow]"
                )
                self.console.print()
                break

            # Basic validation
            if api_key.startswith("sk-ant-"):
                self.config.set_api_key(api_key)
                self.console.print("✓ API key saved to config")
                self.console.print()
                break
            else:
                self.console.print(
                    "[red]Invalid API key format. "
                    "Keys should start with 'sk-ant-'[/red]"
                )

    def _setup_whisper_model(self) -> None:
        """
        Prompt user for Whisper model size preference.
        """
        self.console.print("[bold]Whisper Model Selection[/bold]")
        self.console.print()
        self.console.print(
            "Clarity uses OpenAI's Whisper for transcription. "
            "Choose a model size:\n"
        )
        self.console.print("  • [cyan]tiny[/cyan]   - Fastest, least accurate (~75MB)")
        self.console.print("  • [cyan]base[/cyan]   - Good balance (recommended, ~150MB)")
        self.console.print("  • [cyan]small[/cyan]  - Better accuracy (~500MB)")
        self.console.print("  • [cyan]medium[/cyan] - High accuracy (~1.5GB)")
        self.console.print("  • [cyan]large[/cyan]  - Best accuracy (~3GB)")
        self.console.print()

        model = Prompt.ask(
            "Select model size",
            choices=["tiny", "base", "small", "medium", "large"],
            default="base",
        )

        self.config.set_whisper_model(model)
        self.console.print(f"✓ Whisper model set to: [cyan]{model}[/cyan]")
        self.console.print()

        # Note about download
        self.console.print(
            "[dim]Note: The model will be downloaded automatically "
            "on first transcription.[/dim]"
        )
        self.console.print()

    def _setup_audio_archive(self) -> None:
        """
        Prompt user for audio archival preference.
        """
        self.console.print("[bold]Audio Archive[/bold]")
        self.console.print()
        self.console.print(
            "Should Clarity save copies of your audio recordings?\n"
            "Saved to: ~/.clarity/audio/"
        )
        self.console.print()

        archive = Confirm.ask(
            "Archive audio files?",
            default=True,
        )

        self.config.set_archive_audio(archive)

        if archive:
            self.console.print("✓ Audio files will be archived")
        else:
            self.console.print("✓ Audio files will not be saved")

        self.console.print()

    def check_setup_on_startup(self) -> None:
        """
        Check if setup is complete on CLI startup.

        If not complete, run setup flow.

        Raises:
            SystemExit: If setup incomplete and user declines
        """
        if self.is_first_run():
            try:
                success = self.run_setup()
                if not success:
                    self.console.print(
                        "[red]Setup incomplete. Please try again.[/red]"
                    )
                    sys.exit(1)
            except KeyboardInterrupt:
                sys.exit(1)

    def validate_setup(self) -> bool:
        """
        Validate that setup is complete and correct.

        Returns:
            True if setup is valid

        Prints warnings/errors to console if issues found.
        """
        is_valid = True

        # Check storage
        if not self.storage.storage_exists():
            self.console.print("[red]✗ Storage not initialized[/red]")
            is_valid = False
        else:
            self.console.print("[green]✓ Storage initialized[/green]")

        # Check config
        if not self.config.config_exists():
            self.console.print("[red]✗ Config file not found[/red]")
            is_valid = False
        else:
            self.console.print("[green]✓ Config file exists[/green]")

            # Validate config contents
            messages = self.config.validate_config()
            if messages:
                for key, message in messages.items():
                    self.console.print(f"[yellow]⚠ {message}[/yellow]")
                    # API key warning is not fatal
                    if key != "api_key":
                        is_valid = False
            else:
                self.console.print("[green]✓ Config is valid[/green]")

        return is_valid
