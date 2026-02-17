"""
Session setup orchestration (Ticket 1.3.6).

Complete session setup flow combining all components:
- Phase detection
- Warm-up display
- Topic generation
- Framework assignment
- Focus skill selection
- Session brief display with prep timer
"""

import time
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from clarity.session.focus_skills import get_skill_description, select_focus_skills
from clarity.session.framework_assignment import assign_framework
from clarity.session.phase_config import (
    Framework,
    Phase,
    get_framework_components,
    get_phase_config,
)
from clarity.session.topics import Topic, TopicManager
from clarity.session.warmup import display_warmup_exercises


@dataclass
class SessionBrief:
    """Complete session configuration and parameters."""

    phase: Phase
    topic: Topic
    framework: Framework
    framework_components: list[str]
    focus_skills: list[str]
    skill_descriptions: list[str]
    prep_time_seconds: int
    speaking_duration_range: str  # e.g., "60-90 seconds"
    session_number: int  # Total sessions completed + 1


def detect_current_phase(storage_manager) -> Phase:
    """
    Detect user's current phase based on session history and metrics.

    Args:
        storage_manager: StorageManager instance

    Returns:
        Current Phase

    Logic:
        - No sessions → Phase 1
        - Check transition criteria for phase advancement
        - Phases advance based on session count AND metric thresholds
    """
    try:
        data = storage_manager.read_all()

        # Get current phase from profile (if set)
        current_phase = data.get("profile", {}).get("current_phase", "PHASE_1")

        # Convert string to enum
        phase_map = {
            "PHASE_1": Phase.PHASE_1,
            "PHASE_2": Phase.PHASE_2,
            "PHASE_3": Phase.PHASE_3,
            "MAINTENANCE": Phase.MAINTENANCE,
        }

        return phase_map.get(current_phase, Phase.PHASE_1)

    except Exception:
        # Default to Phase 1 if storage not initialized
        return Phase.PHASE_1


def check_phase_transition(storage_manager, current_phase: Phase) -> Phase | None:
    """
    Check if user meets criteria to advance to next phase.

    Args:
        storage_manager: StorageManager instance
        current_phase: Current phase

    Returns:
        Next phase if transition criteria met, None otherwise
    """
    try:
        data = storage_manager.read_all()
        sessions = data.get("sessions", [])

        if not sessions:
            return None

        config = get_phase_config(current_phase)

        # Check minimum session count
        phase_sessions = [
            s for s in sessions if s.get("phase") == current_phase.name
        ]

        if len(phase_sessions) < config.min_sessions:
            return None

        # Check metric thresholds (last 5 sessions)
        recent_sessions = sessions[-5:] if len(sessions) >= 5 else sessions

        # Evaluate transition criteria
        meets_criteria = True
        for metric_name, threshold in config.transition_criteria.items():
            # Extract metric values
            values = []
            for session in recent_sessions:
                metrics = session.get("metrics", {})
                if metric_name in metrics:
                    values.append(metrics[metric_name])

            if not values:
                meets_criteria = False
                break

            avg_value = sum(values) / len(values)

            # Check threshold (some metrics are "lower is better")
            if metric_name in ["filler_rate", "maze_rate", "hedging_frequency"]:
                if avg_value > threshold:
                    meets_criteria = False
                    break
            else:
                if avg_value < threshold:
                    meets_criteria = False
                    break

        if meets_criteria:
            # Advance to next phase
            phase_sequence = [
                Phase.PHASE_1,
                Phase.PHASE_2,
                Phase.PHASE_3,
                Phase.MAINTENANCE,
            ]
            current_idx = phase_sequence.index(current_phase)
            if current_idx < len(phase_sequence) - 1:
                return phase_sequence[current_idx + 1]

        return None

    except Exception:
        return None


def setup_session(
    storage_manager,
    topic_override: str | None = None,
    console: Console | None = None,
) -> SessionBrief:
    """
    Run complete session setup flow.

    Args:
        storage_manager: StorageManager instance
        topic_override: Optional manual topic (from --topic flag)
        console: Rich Console instance

    Returns:
        SessionBrief with all session parameters
    """
    if console is None:
        console = Console()

    # 1. Detect current phase
    current_phase = detect_current_phase(storage_manager)
    config = get_phase_config(current_phase)

    # Check for phase transition
    next_phase = check_phase_transition(storage_manager, current_phase)
    if next_phase:
        console.print(
            f"\n[green]🎉 Congratulations! You've advanced to {next_phase.name}![/green]\n"
        )
        current_phase = next_phase
        config = get_phase_config(current_phase)

        # Update storage
        try:
            data = storage_manager.read_all()
            if "profile" not in data:
                data["profile"] = {}
            data["profile"]["current_phase"] = current_phase.name
            storage_manager._atomic_write(storage_manager.sessions_file, data)
        except Exception:
            pass

    # 2. Display warm-up exercises
    console.print(f"\n[bold cyan]Phase {current_phase.value}:[/bold cyan] {config.name}")
    console.print(f"[dim]{config.goals}[/dim]\n")
    display_warmup_exercises(config, console)

    # 3. Generate topic
    topic_manager = TopicManager(storage_manager)
    allowed_types = None  # All types for now (phase filtering can be added later)

    topic = topic_manager.get_topic(
        allowed_types=allowed_types, override_title=topic_override
    )

    # 4. Assign framework
    framework = assign_framework(topic, config.available_frameworks)
    framework_components = get_framework_components(framework)

    # 5. Select focus skills
    focus_skills = select_focus_skills(config, storage_manager, num_skills=2)
    skill_descriptions = [get_skill_description(skill) for skill in focus_skills]

    # 6. Get session number
    try:
        data = storage_manager.read_all()
        session_number = len(data.get("sessions", [])) + 1
    except Exception:
        session_number = 1

    # 7. Build session brief
    speaking_range = f"{config.speaking_duration_min}-{config.speaking_duration_max} seconds"

    brief = SessionBrief(
        phase=current_phase,
        topic=topic,
        framework=framework,
        framework_components=framework_components,
        focus_skills=focus_skills,
        skill_descriptions=skill_descriptions,
        prep_time_seconds=config.prep_time_seconds,
        speaking_duration_range=speaking_range,
        session_number=session_number,
    )

    # 8. Display session brief
    display_session_brief(brief, console)

    # 9. Prep timer countdown (if prep time > 0)
    if config.prep_time_seconds > 0:
        run_prep_timer(config.prep_time_seconds, console)

    return brief


def display_session_brief(brief: SessionBrief, console: Console) -> None:
    """
    Display complete session brief.

    Args:
        brief: SessionBrief object
        console: Rich Console instance
    """
    # Build brief content
    content = Text()

    # Session number
    content.append(f"Session #{brief.session_number}\n", style="bold yellow")
    content.append("\n")

    # Topic
    content.append("📋 Topic: ", style="bold cyan")
    content.append(f"{brief.topic.title}\n", style="white")
    content.append(f"   {brief.topic.description}\n", style="dim")
    content.append("\n")

    # Framework
    content.append("🏗️  Framework: ", style="bold cyan")
    content.append(f"{brief.framework.value}\n", style="yellow")
    for i, component in enumerate(brief.framework_components, start=1):
        content.append(f"   {i}. {component}\n", style="dim")
    content.append("\n")

    # Focus Skills
    content.append("🎯 Focus Skills:\n", style="bold cyan")
    for i, (skill, desc) in enumerate(
        zip(brief.focus_skills, brief.skill_descriptions, strict=True), start=1
    ):
        content.append(f"   {i}. ", style="bold yellow")
        content.append(f"{skill}\n", style="white")
        content.append(f"      {desc}\n", style="dim")
    content.append("\n")

    # Parameters
    content.append("⏱️  Parameters:\n", style="bold cyan")
    content.append("   • Prep time: ", style="dim")
    content.append(f"{brief.prep_time_seconds} seconds\n", style="white")
    content.append("   • Speaking duration: ", style="dim")
    content.append(f"{brief.speaking_duration_range}\n", style="white")

    # Render panel
    panel = Panel(
        content,
        title=f"[bold]Session Brief — {brief.phase.name}[/bold]",
        border_style="green",
        padding=(1, 2),
    )

    console.print()
    console.print(panel)
    console.print()


def run_prep_timer(seconds: int, console: Console) -> None:
    """
    Run preparation timer countdown.

    Args:
        seconds: Number of seconds to count down
        console: Rich Console instance
    """
    console.print(
        f"[yellow]⏳ Preparation time: {seconds} seconds[/yellow]"
    )
    console.print("[dim]Use this time to organize your thoughts...[/dim]\n")

    try:
        # Simple countdown with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Preparing... ({seconds}s remaining)", total=None
            )

            for remaining in range(seconds, 0, -1):
                progress.update(
                    task, description=f"Preparing... ({remaining}s remaining)"
                )
                time.sleep(1)

            progress.update(task, description="Prep time complete!")

        console.print("\n[green]✓ Prep time complete! Ready to speak.[/green]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Timer interrupted.[/yellow]\n")


def is_baseline_session(storage_manager) -> bool:
    """
    Check if this is a baseline session (no baseline recorded yet).

    Args:
        storage_manager: StorageManager instance

    Returns:
        True if no baseline exists, False otherwise
    """
    from clarity.session.baseline import has_baseline

    try:
        return not has_baseline(storage_manager)
    except Exception:
        return True  # Assume baseline if storage not initialized
