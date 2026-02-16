"""
Practice command - main workflow orchestrator (Ticket 1.6.1).

Coordinates: setup → warm-up → transcribe → analyze → feedback → persist.
"""

from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from clarity.analysis import (
    ClaudeAPIClient,
    build_analysis_prompt,
    parse_analysis_response,
    validate_analysis_response,
)
from clarity.config import ConfigManager
from clarity.feedback import (
    calculate_phase_metrics,
    calculate_trends,
    check_personal_best,
    detect_overcorrection,
    display_personal_bests,
    display_phase_milestone,
    display_scorecard,
    display_tips,
    display_trends,
    prompt_comfort_rating,
)
from clarity.session import (
    get_baseline_metrics,
    get_phase_config,
    is_baseline_session,
    setup_baseline_session,
    setup_session,
)
from clarity.storage import StorageManager
from clarity.transcription import WhisperService, calculate_metrics


def run_practice_session(
    audio_path: Path | str | None = None,
    topic_override: str | None = None,
    storage_dir: Path | None = None,
) -> None:
    """
    Run complete practice session workflow.

    Args:
        audio_path: Path to .webm audio file (optional - will prompt if None)
        topic_override: Custom topic (optional - uses rotation if None)
        storage_dir: Custom storage directory (optional - uses default if None)

    Raises:
        FileNotFoundError: If audio file doesn't exist
        ValueError: If API key is missing
        RuntimeError: If transcription or analysis fails
    """
    console = Console()

    # Initialize managers
    storage = StorageManager(storage_dir)
    config = ConfigManager()

    # Ensure storage is initialized
    if not storage.storage_exists():
        storage.init_storage()

    # Ensure config exists
    if not config.config_exists():
        config.init_config()

    # Check if baseline session
    if is_baseline_session(storage):
        console.print("\n[bold green]Welcome to Clarity![/bold green]")
        console.print("Let's establish your baseline metrics.\n")
        _run_baseline_session(storage, config, console)
        return

    # === 1. SESSION SETUP ===
    console.print("\n[bold cyan]═══ Session Setup ═══[/bold cyan]\n")

    brief = setup_session(
        storage_manager=storage,
        topic_override=topic_override,
        console=console,
    )

    # === 2. PROMPT FOR RECORDING ===
    console.print("[bold yellow]📱 Record your response now[/bold yellow]")
    console.print(
        "Record yourself speaking on the topic using your audio recorder "
        "(Android Recorder, Voice Memos, etc.)"
    )
    console.print()

    # Get audio path
    if audio_path is None:
        from rich.prompt import Prompt

        audio_path = Prompt.ask("Path to your .webm audio file")

    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # === 3. TRANSCRIPTION ===
    console.print("\n[bold cyan]═══ Transcription ═══[/bold cyan]\n")

    whisper_model = config.get_whisper_model()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(f"Transcribing with {whisper_model} model...", total=None)

        whisper = WhisperService(model_size=whisper_model)
        transcription_result = whisper.transcribe_file(
            audio_path, show_progress=False
        )

    console.print(f"[green]✓[/green] Transcribed {transcription_result.word_count} words")
    console.print(
        f"[dim]Duration: {transcription_result.duration_seconds:.1f}s, "
        f"WPM: {transcription_result.duration_seconds / 60 * transcription_result.word_count:.1f}[/dim]"
    )

    # === 4. ANALYSIS ===
    console.print("\n[bold cyan]═══ Analysis ═══[/bold cyan]\n")

    # Build prompt
    phase_config = get_phase_config(brief.phase)
    baseline = get_baseline_metrics(storage)
    recent_sessions = storage.get_recent_sessions(n=5)

    prompt = build_analysis_prompt(
        phase_config=phase_config,
        framework=brief.framework,
        transcript=transcription_result.transcript,
        baseline_metrics=baseline,
        recent_metrics=[s.get("metrics", {}) for s in recent_sessions],
    )

    # Call Claude API
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Analyzing with Claude...", total=None)

        client = ClaudeAPIClient()
        response = client.analyze_transcript(
            prompt=prompt,
            transcript=transcription_result.transcript,
            temperature=0.0,
        )

    # Validate and parse response
    errors = validate_analysis_response(response)
    if errors:
        console.print("[red]⚠ Warning: Analysis response validation failed:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        console.print("\n[yellow]Using raw response...[/yellow]")

    analysis_result = parse_analysis_response(response)

    console.print("[green]✓[/green] Analysis complete")

    # === 5. FEEDBACK & SCORING ===
    console.print("\n[bold cyan]═══ Feedback & Scoring ═══[/bold cyan]\n")

    # Display scorecard
    display_scorecard(analysis_result, phase_config, console)

    # Display tips
    display_tips(analysis_result.tips, console)

    # Display trends
    all_sessions = storage.read_sessions()
    trends = calculate_trends(analysis_result, baseline, recent_sessions)
    display_trends(trends, console)

    # Check for personal bests
    personal_bests = check_personal_best(analysis_result, all_sessions)
    if personal_bests:
        display_personal_bests(personal_bests, console)

    # Phase milestone
    phase_metrics = calculate_phase_metrics(all_sessions, brief.phase)
    sessions_in_phase = len([s for s in all_sessions if s.get("phase") == brief.phase.name])
    display_phase_milestone(phase_config, sessions_in_phase, phase_metrics, console)

    # Overcorrection detection
    detect_overcorrection(all_sessions, console)

    # === 6. COMFORT RATING ===
    comfort_rating = prompt_comfort_rating(console)

    # === 7. PERSIST SESSION ===
    session_data = {
        "topic": brief.topic.title,
        "topic_id": brief.topic.topic_id,
        "framework": brief.framework.value,
        "phase": brief.phase.name,
        "transcript": transcription_result.transcript,
        "word_count": transcription_result.word_count,
        "duration_seconds": transcription_result.duration_seconds,
        "metrics": {
            "composite_score": analysis_result.composite_score,
            "filler_rate": analysis_result.filler_rate,
            "filler_percentage": analysis_result.filler_percentage,
            "filler_count": analysis_result.filler_count,
            "speaking_rate_wpm": analysis_result.speaking_rate_wpm,
            "framework_completion": 100 if analysis_result.framework_completion else 0,
            "comfort_rating": comfort_rating,
        },
        "analysis": {
            "dimension_scores": [
                {
                    "dimension": ds.dimension,
                    "score": ds.score,
                    "rating": ds.rating,
                    "feedback": ds.feedback,
                }
                for ds in analysis_result.dimension_scores
            ],
            "tips": [
                {
                    "title": tip.title,
                    "explanation": tip.explanation,
                    "transcript_excerpt": tip.transcript_excerpt,
                    "technique": tip.technique,
                }
                for tip in analysis_result.tips
            ],
        },
    }

    # Add phase-specific metrics
    if analysis_result.maze_count is not None:
        session_data["metrics"]["maze_count"] = analysis_result.maze_count
        session_data["metrics"]["maze_rate"] = analysis_result.maze_rate

    if analysis_result.hedging_count is not None:
        session_data["metrics"]["hedging_count"] = analysis_result.hedging_count
        session_data["metrics"]["hedging_rate"] = analysis_result.hedging_rate

    if analysis_result.pause_quality_score is not None:
        session_data["metrics"]["pause_quality_score"] = analysis_result.pause_quality_score

    storage.append_session(session_data)

    # Archive audio if configured
    if config.should_archive_audio():
        storage.archive_audio(audio_path)

    # === 8. COMPLETION ===
    console.print("\n[bold green]✓ Session complete![/bold green]")
    console.print(
        f"[dim]Session #{storage.read_all()['total_sessions']} saved to {storage.sessions_file}[/dim]\n"
    )


def _run_baseline_session(
    storage: StorageManager,
    config: ConfigManager,
    console: Console,
) -> None:
    """
    Run simplified baseline session.

    Args:
        storage: StorageManager instance
        config: ConfigManager instance
        console: Rich Console instance
    """
    brief = setup_baseline_session(console)

    # Prompt for recording
    console.print("[bold yellow]📱 Record your response now[/bold yellow]")
    console.print()

    from rich.prompt import Prompt

    audio_path = Prompt.ask("Path to your .webm audio file")
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Transcribe
    console.print("\n[bold cyan]Transcribing...[/bold cyan]\n")
    whisper = WhisperService(model_size=config.get_whisper_model())
    transcription_result = whisper.transcribe_file(audio_path, show_progress=True)

    console.print(f"\n[green]✓[/green] Transcribed {transcription_result.word_count} words")

    # Calculate metrics
    speaking_metrics = calculate_metrics(transcription_result)

    # Store baseline
    baseline_metrics = {
        "filler_rate": speaking_metrics.filler_rate,
        "filler_percentage": (speaking_metrics.filler_count / transcription_result.word_count) * 100
        if transcription_result.word_count > 0
        else 0,
        "speaking_rate_wpm": transcription_result.word_count
        / (transcription_result.duration_seconds / 60)
        if transcription_result.duration_seconds > 0
        else 0,
        "framework_completion": 60,  # Placeholder for baseline
    }

    from clarity.session import store_baseline_metrics

    store_baseline_metrics(storage, baseline_metrics)

    # Display baseline
    console.print("\n[bold green]✓ Baseline established![/bold green]")
    console.print(f"  • Filler rate: {baseline_metrics['filler_rate']:.1f}/min")
    console.print(f"  • Speaking rate: {baseline_metrics['speaking_rate_wpm']:.1f} WPM")
    console.print("\nYou're ready to start your practice journey!\n")
