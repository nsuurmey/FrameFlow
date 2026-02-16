"""
Warm-up exercise display (Ticket 1.3.4).

Renders phase-specific warm-up exercises with rich formatting.
"""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from clarity.session.phase_config import PhaseConfig


def display_warmup_exercises(
    config: PhaseConfig, console: Console | None = None
) -> None:
    """
    Display warm-up exercises for a phase with rich formatting.

    Args:
        config: PhaseConfig with warm_up_exercises
        console: Rich Console instance (creates new one if None)
    """
    if console is None:
        console = Console()

    # Create header
    header = Text()
    header.append("🎯 Warm-Up Exercises", style="bold cyan")
    header.append(f" — {config.name} Phase\n", style="dim")

    # Build exercise list
    content = Text()
    for i, exercise in enumerate(config.warm_up_exercises, start=1):
        # Exercise name
        content.append(f"{i}. ", style="bold yellow")
        content.append(f"{exercise.name}", style="bold white")
        content.append(f" ({exercise.duration_estimate})\n", style="dim")

        # Instructions
        content.append(f"   {exercise.instructions}\n", style="")
        if i < len(config.warm_up_exercises):
            content.append("\n")

    # Render panel
    panel = Panel(
        content,
        title="[bold]Warm-Up Routine[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)
    console.print()


def display_warmup_summary(
    config: PhaseConfig, console: Console | None = None
) -> None:
    """
    Display brief warm-up summary (for session brief).

    Args:
        config: PhaseConfig with warm_up_exercises
        console: Rich Console instance (creates new one if None)
    """
    if console is None:
        console = Console()

    total_time = sum(
        _parse_duration(ex.duration_estimate) for ex in config.warm_up_exercises
    )

    console.print(
        f"[cyan]Warm-up:[/cyan] {len(config.warm_up_exercises)} exercises "
        f"(~{total_time} seconds total)"
    )


def _parse_duration(duration_str: str) -> int:
    """
    Parse duration estimate string to seconds.

    Args:
        duration_str: Duration string like "30 seconds" or "1 minute"

    Returns:
        Duration in seconds (approximate)

    Examples:
        >>> _parse_duration("30 seconds")
        30
        >>> _parse_duration("1 minute")
        60
    """
    duration_str = duration_str.lower()

    # Extract number
    import re

    match = re.search(r"(\d+)", duration_str)
    if not match:
        return 30  # Default fallback

    num = int(match.group(1))

    # Check unit
    if "minute" in duration_str:
        return num * 60
    else:
        return num  # Assume seconds


def get_warmup_checklist(config: PhaseConfig) -> list[str]:
    """
    Get warm-up exercises as a checklist.

    Args:
        config: PhaseConfig with warm_up_exercises

    Returns:
        List of exercise names for checklist display
    """
    return [ex.name for ex in config.warm_up_exercises]
