"""
Baseline session flow (Ticket 1.3.7).

Handles first-run detection and simplified baseline session.
Skips warm-up, uses standard topic, records baseline metrics.
"""

from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from clarity.session.phase_config import (
    Framework,
    Phase,
    get_framework_components,
    get_phase_config,
)
from clarity.session.topics import Topic

# Standard baseline topic (consistent across all users)
BASELINE_TOPIC = Topic(
    title="Explain Your Current Role",
    description="Describe what you do in your current job or most recent position. Explain your key responsibilities and what a typical day looks like.",
    topic_type="explain",
    topic_id=0,  # Reserved ID for baseline
)


@dataclass
class BaselineSessionBrief:
    """Simplified session configuration for baseline."""

    topic: Topic
    framework: Framework
    framework_components: list[str]
    speaking_duration_range: str
    is_baseline: bool = True


def setup_baseline_session(console: Console | None = None) -> BaselineSessionBrief:
    """
    Set up a simplified baseline session.

    Baseline sessions:
    - Skip warm-up exercises
    - Use standard topic ("Explain Your Current Role")
    - Use PREP framework
    - Record metrics for baseline comparison

    Args:
        console: Rich Console instance

    Returns:
        BaselineSessionBrief with session parameters
    """
    if console is None:
        console = Console()

    # Get Phase 1 config for duration parameters
    config = get_phase_config(Phase.PHASE_1)

    # Use PREP framework for baseline
    framework = Framework.PREP
    framework_components = get_framework_components(framework)

    # Build brief
    speaking_range = f"{config.speaking_duration_min}-{config.speaking_duration_max} seconds"

    brief = BaselineSessionBrief(
        topic=BASELINE_TOPIC,
        framework=framework,
        framework_components=framework_components,
        speaking_duration_range=speaking_range,
    )

    # Display baseline session brief
    display_baseline_brief(brief, console)

    return brief


def display_baseline_brief(
    brief: BaselineSessionBrief, console: Console
) -> None:
    """
    Display baseline session brief.

    Args:
        brief: BaselineSessionBrief object
        console: Rich Console instance
    """
    # Build content
    content = Text()

    # Welcome message
    content.append("Welcome to your first practice session!\n\n", style="bold green")

    content.append(
        "This is a baseline session to establish your starting metrics.\n",
        style="dim",
    )
    content.append("Just relax and speak naturally — no warm-up needed.\n\n", style="dim")

    # Topic
    content.append("📋 Topic: ", style="bold cyan")
    content.append(f"{brief.topic.title}\n", style="white")
    content.append(f"   {brief.topic.description}\n", style="dim")
    content.append("\n")

    # Framework
    content.append("🏗️  Framework: ", style="bold cyan")
    content.append(f"{brief.framework.value}\n", style="yellow")
    content.append("   Try to hit these components:\n", style="dim")
    for i, component in enumerate(brief.framework_components, start=1):
        content.append(f"   {i}. {component}\n", style="dim")
    content.append("\n")

    # Parameters
    content.append("⏱️  Speaking Duration: ", style="bold cyan")
    content.append(f"{brief.speaking_duration_range}\n", style="white")
    content.append("\n")

    # Instructions
    content.append("📝 Instructions:\n", style="bold cyan")
    content.append("   1. Take a moment to think about your response\n", style="dim")
    content.append("   2. Record yourself speaking on the topic\n", style="dim")
    content.append("   3. Upload the .webm file when ready\n", style="dim")
    content.append("\n")

    content.append(
        "Your baseline metrics will help track your progress over time.\n",
        style="italic dim",
    )

    # Render panel
    panel = Panel(
        content,
        title="[bold]Baseline Session[/bold]",
        border_style="green",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)
    console.print()


def store_baseline_metrics(storage_manager, metrics: dict) -> None:
    """
    Store baseline metrics in user profile.

    Args:
        storage_manager: StorageManager instance
        metrics: Dictionary of baseline metrics

    Example metrics:
        {
            "filler_rate": 8.5,
            "filler_percentage": 4.2,
            "framework_completion": 60,
            "speaking_rate_wpm": 145,
        }
    """
    try:
        data = storage_manager.read_all()

        if "profile" not in data:
            data["profile"] = {}

        data["profile"]["baseline"] = metrics
        data["profile"]["baseline_completed"] = True

        # Write updated data using atomic write
        storage_manager._atomic_write(storage_manager.sessions_file, data)

    except Exception as e:
        raise RuntimeError(f"Failed to store baseline metrics: {e}") from e


def has_baseline(storage_manager) -> bool:
    """
    Check if user has completed baseline session.

    Args:
        storage_manager: StorageManager instance

    Returns:
        True if baseline exists, False otherwise
    """
    try:
        data = storage_manager.read_all()
        return data.get("profile", {}).get("baseline_completed", False)
    except Exception:
        return False


def get_baseline_metrics(storage_manager) -> dict | None:
    """
    Get stored baseline metrics.

    Args:
        storage_manager: StorageManager instance

    Returns:
        Baseline metrics dict if exists, None otherwise
    """
    try:
        data = storage_manager.read_all()
        return data.get("profile", {}).get("baseline")
    except Exception:
        return None
