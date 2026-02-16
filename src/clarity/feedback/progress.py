"""
Progress tracking utilities (Tickets 1.5.4, 1.5.5, 1.5.6).

Phase milestones, overcorrection detection, and comfort rating.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.text import Text

from clarity.session.phase_config import Phase, PhaseConfig


def display_phase_milestone(
    phase_config: PhaseConfig,
    sessions_in_phase: int,
    recent_metrics: dict[str, float],
    console: Console | None = None,
) -> None:
    """
    Display phase progression and milestone status (Ticket 1.5.4).

    Args:
        phase_config: Current PhaseConfig
        sessions_in_phase: Number of sessions completed in current phase
        recent_metrics: Average metrics from last 5 sessions
        console: Rich Console instance
    """
    if console is None:
        console = Console()

    if phase_config.phase == Phase.MAINTENANCE:
        # No milestones in maintenance
        return

    content = Text()

    # Progress toward minimum sessions
    content.append(f"Phase {phase_config.phase.value} Progress\n\n", style="bold cyan")

    # Sessions completed
    min_sessions = phase_config.min_sessions
    content.append(f"Sessions: {sessions_in_phase}/{min_sessions}\n", style="white")

    # Check transition criteria
    content.append("\n")
    content.append("Transition Criteria:\n", style="bold")

    criteria_met = 0
    total_criteria = len(phase_config.transition_criteria)

    for metric_name, threshold in phase_config.transition_criteria.items():
        current_value = recent_metrics.get(metric_name, 0)

        # Determine if met (some metrics are "lower is better")
        if metric_name in ["filler_rate", "maze_rate", "hedging_frequency"]:
            met = current_value <= threshold
        else:
            met = current_value >= threshold

        if met:
            criteria_met += 1

        status = "✓" if met else "✗"
        color = "green" if met else "yellow"

        content.append(
            f"  {status} {metric_name}: {current_value:.1f} "
            f"({'≤' if metric_name in ['filler_rate', 'maze_rate', 'hedging_frequency'] else '≥'} {threshold})\n",
            style=color,
        )

    # Summary
    content.append("\n")
    if sessions_in_phase >= min_sessions and criteria_met == total_criteria:
        content.append("🎉 Ready to advance to next phase!\n", style="bold green")
    else:
        sessions_remaining = max(0, min_sessions - sessions_in_phase)
        if sessions_remaining > 0:
            content.append(
                f"Complete {sessions_remaining} more sessions to unlock advancement.\n",
                style="dim",
            )
        else:
            content.append(
                f"Meet {total_criteria - criteria_met} more criteria to advance.\n",
                style="dim",
            )

    panel = Panel(
        content,
        title="[bold]Phase Milestone Tracker[/bold]",
        border_style="cyan",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)
    console.print()


def detect_overcorrection(
    recent_sessions: list[dict],
    console: Console | None = None,
) -> bool:
    """
    Detect overcorrection (filler rate = 0 for 3+ sessions) (Ticket 1.5.5).

    Args:
        recent_sessions: Last N sessions
        console: Rich Console instance

    Returns:
        True if overcorrection detected, False otherwise
    """
    if len(recent_sessions) < 3:
        return False

    # Check last 3 sessions for zero filler rate
    zero_count = 0
    for session in recent_sessions[-3:]:
        metrics = session.get("metrics", {})
        filler_rate = metrics.get("filler_rate", 0)
        if filler_rate == 0:
            zero_count += 1

    if zero_count >= 3:
        if console:
            console.print()
            console.print(
                "[yellow]⚠ Overcorrection Alert:[/yellow] "
                "You've had zero fillers in your last 3 sessions. "
                "Some fillers are natural — don't over-monitor!"
            )
            console.print()
        return True

    return False


def prompt_comfort_rating(console: Console | None = None) -> int:
    """
    Prompt user for comfort rating (1-10) (Ticket 1.5.6).

    Args:
        console: Rich Console instance

    Returns:
        Comfort rating (1-10)
    """
    if console is None:
        console = Console()

    console.print()
    console.print("[bold cyan]How comfortable did you feel during this session?[/bold cyan]")
    console.print("[dim](1 = very uncomfortable, 10 = very comfortable)[/dim]")

    while True:
        try:
            rating = IntPrompt.ask("Your rating", console=console, default=5)
            if 1 <= rating <= 10:
                return rating
            else:
                console.print("[red]Please enter a number between 1 and 10.[/red]")
        except (ValueError, KeyboardInterrupt):
            console.print("[yellow]Using default rating of 5.[/yellow]")
            return 5


def calculate_phase_metrics(
    sessions: list[dict],
    current_phase: Phase,
) -> dict[str, float]:
    """
    Calculate average metrics for sessions in current phase.

    Args:
        sessions: All sessions
        current_phase: Current phase

    Returns:
        Dictionary of metric_name -> average_value
    """
    # Filter sessions for current phase
    phase_sessions = [s for s in sessions if s.get("phase") == current_phase.name]

    if not phase_sessions:
        return {}

    # Get last 5 sessions in phase
    recent = phase_sessions[-5:] if len(phase_sessions) >= 5 else phase_sessions

    # Calculate averages
    metrics_sum: dict[str, list[float]] = {}
    for session in recent:
        metrics = session.get("metrics", {})
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if key not in metrics_sum:
                    metrics_sum[key] = []
                metrics_sum[key].append(value)

    # Average
    result = {}
    for key, values in metrics_sum.items():
        result[key] = sum(values) / len(values)

    return result
