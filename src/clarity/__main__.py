"""
Main entry point for the Clarity CLI.

Usage:
    python -m clarity --help
    python -m clarity practice
    python -m clarity baseline
    python -m clarity history
    python -m clarity status
    python -m clarity review <session_id>
    python -m clarity analyze <file.webm>  # Legacy MVP0 command
    python -m clarity report                # Legacy MVP0 command
"""

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from clarity.analyzers.analyzer import ClarityAnalyzer
from clarity.audio_loader import AudioLoader, FFmpegNotFoundError
from clarity.reporting.csv_logger import CSVLogger
from clarity.reporting.plotter import MetricsPlotter
from clarity.reporting.report_generator import ReportGenerator
from clarity.setup import FirstRunSetup

# Initialize Typer app and Rich console
app = typer.Typer(
    name="clarity",
    help="Speaking clarity practice tool - improve your extemporaneous speaking skills",
    add_completion=False,
)
console = Console()

# Global setup instance
_setup: FirstRunSetup | None = None


def get_setup() -> FirstRunSetup:
    """Get or create the FirstRunSetup instance."""
    global _setup
    if _setup is None:
        _setup = FirstRunSetup(console=console)
    return _setup


@app.callback(invoke_without_command=True)
def check_first_run(ctx: typer.Context):
    """
    Check for first-run setup before executing commands.

    Runs automatically before every command.
    """
    # Skip setup check for --help and --version
    if ctx.resilient_parsing:
        return

    # Skip setup check for legacy commands (analyze, report)
    # They don't need storage/config
    if ctx.invoked_subcommand in ["analyze", "report"]:
        return

    # Run first-run setup if needed
    setup = get_setup()
    if setup.is_first_run() and ctx.invoked_subcommand:
        setup.check_setup_on_startup()


# ============================================================================
# MVP1 Commands (stubs for now)
# ============================================================================


@app.command()
def practice(
    topic: str | None = typer.Option(
        None, "--topic", help="Override the daily topic"
    ),
    paste: bool = typer.Option(
        False, "--paste", help="Paste transcript instead of uploading audio"
    ),
):
    """
    Complete a full daily practice session.

    Workflow: setup → warm-up → record → transcribe → analyze → feedback
    """
    console.print(Panel.fit(
        "[bold cyan]Practice Session[/bold cyan]\n\n"
        "🚧 [yellow]Coming in MVP1[/yellow]\n\n"
        "This command will guide you through a complete daily practice session:\n"
        "  • Phase-appropriate warm-up exercises\n"
        "  • Generated topic and framework\n"
        "  • Audio upload and transcription\n"
        "  • AI-powered analysis and scoring\n"
        "  • Personalized feedback and tips",
        title="✨ Practice",
    ))


@app.command()
def baseline(
    force: bool = typer.Option(False, "--force", help="Re-record baseline (replaces existing)"),
):
    """
    Record your baseline session (first-time setup).

    The baseline is used to measure your progress over time.
    """
    console.print(Panel.fit(
        "[bold cyan]Baseline Recording[/bold cyan]\n\n"
        "🚧 [yellow]Coming in MVP1[/yellow]\n\n"
        "This command will record your baseline speaking metrics:\n"
        "  • Simple speaking task (no pressure)\n"
        "  • Full analysis of your current abilities\n"
        "  • Reference point for tracking improvement",
        title="📊 Baseline",
    ))


@app.command()
def history(
    limit: int = typer.Option(10, "--limit", "-n", help="Number of sessions to show"),
    all_sessions: bool = typer.Option(False, "--all", help="Show all sessions"),
):
    """
    View your practice session history.

    Shows recent sessions with dates, topics, scores, and phase info.
    """
    console.print(Panel.fit(
        "[bold cyan]Session History[/bold cyan]\n\n"
        "🚧 [yellow]Coming in MVP1[/yellow]\n\n"
        "This command will display your practice history:\n"
        "  • Session dates and topics\n"
        "  • Composite scores\n"
        "  • Current phase and streak\n"
        "  • Trend indicators (↑/↓)",
        title="📜 History",
    ))


@app.command()
def status():
    """
    View your current phase, streak, and progress.

    Shows where you are in the 90-day program and what's next.
    """
    console.print(Panel.fit(
        "[bold cyan]Current Status[/bold cyan]\n\n"
        "🚧 [yellow]Coming in MVP1[/yellow]\n\n"
        "This command will show:\n"
        "  • Current phase and day count\n"
        "  • Active streak\n"
        "  • Progress toward next phase\n"
        "  • Recommended focus areas",
        title="📈 Status",
    ))


@app.command()
def review(
    session_id: str = typer.Argument(..., help="Session ID to review"),
    export: bool = typer.Option(False, "--export", help="Export to markdown file"),
):
    """
    Review detailed analysis from a past session.

    Re-displays the full scorecard, tips, and transcript.
    """
    console.print(Panel.fit(
        f"[bold cyan]Review Session: {session_id}[/bold cyan]\n\n"
        "🚧 [yellow]Coming in MVP1[/yellow]\n\n"
        "This command will display:\n"
        "  • Full scorecard with dimension scores\n"
        "  • Actionable tips with examples\n"
        "  • Complete transcript\n"
        "  • Trends vs. previous sessions",
        title="🔍 Review",
    ))


@app.command()
def weekly():
    """
    Generate a weekly summary report.

    Aggregate metrics and insights for the current week.
    """
    console.print(Panel.fit(
        "[bold cyan]Weekly Summary[/bold cyan]\n\n"
        "🚧 [yellow]Coming in MVP1[/yellow]\n\n"
        "This command will show:\n"
        "  • Sessions completed this week\n"
        "  • Average scores by dimension\n"
        "  • Best and worst dimensions\n"
        "  • Streak status",
        title="📅 Weekly",
    ))


@app.command()
def setup(
    force: bool = typer.Option(
        False, "--force", help="Re-run setup even if already configured"
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate current setup without changing"
    ),
):
    """
    Run or validate first-time setup.

    Use this to reconfigure Clarity or check your current setup.
    """
    setup_instance = get_setup()

    if validate:
        console.print("\n[bold]Validating Clarity Setup[/bold]\n")
        is_valid = setup_instance.validate_setup()
        console.print()

        if is_valid:
            console.print("[green]✓ Setup is valid and complete![/green]\n")
            raise typer.Exit(0)
        else:
            console.print(
                "[yellow]Setup has issues. Run 'clarity setup --force' to reconfigure.[/yellow]\n"
            )
            raise typer.Exit(1)

    if not force and not setup_instance.is_first_run():
        console.print("\n[yellow]Clarity is already set up.[/yellow]")
        console.print("Use [cyan]--force[/cyan] to reconfigure.\n")
        raise typer.Exit(0)

    try:
        setup_instance.run_setup()
        raise typer.Exit(0)
    except KeyboardInterrupt:
        raise typer.Exit(1) from None


# ============================================================================
# MVP0 Legacy Commands (keep working)
# ============================================================================


def format_results(results: dict) -> str:
    """Format analysis results for display."""
    lines = []

    # Transcript
    lines.append("\n" + "=" * 60)
    lines.append("TRANSCRIPT")
    lines.append("=" * 60)
    lines.append(results["transcript"])

    # Speaking Rate
    lines.append("\n" + "=" * 60)
    lines.append("SPEAKING RATE")
    lines.append("=" * 60)
    sr = results["speaking_rate"]
    lines.append(f"  Words: {sr['word_count']}")
    lines.append(f"  WPM: {sr['wpm']:.1f}")
    lines.append(f"  Duration: {sr['duration_seconds']:.2f}s")

    # Filler Words
    lines.append("\n" + "=" * 60)
    lines.append("FILLER WORDS")
    lines.append("=" * 60)
    fillers = results["fillers"]
    lines.append(f"  Total: {fillers['total_filler_count']}")
    if fillers["filler_breakdown"]:
        lines.append("  Breakdown:")
        for word, count in sorted(
            fillers["filler_breakdown"].items(), key=lambda x: x[1], reverse=True
        ):
            lines.append(f"    - {word}: {count}")
    else:
        lines.append("  (No fillers detected)")

    # Pauses
    lines.append("\n" + "=" * 60)
    lines.append("PAUSES")
    lines.append("=" * 60)
    pauses = results["pauses"]
    lines.append(f"  Count: {pauses['pause_count']}")
    lines.append(f"  Total duration: {pauses['total_pause_duration']:.2f}s")
    if pauses["pause_count"] > 0:
        lines.append(f"  Average duration: {pauses['avg_pause_duration']:.2f}s")
    lines.append(f"  Percentage: {pauses['pause_percentage']:.1f}%")

    # Energy
    lines.append("\n" + "=" * 60)
    lines.append("ENERGY/VOLUME")
    lines.append("=" * 60)
    energy = results["energy"]
    lines.append(f"  Mean: {energy['mean_energy_db']:.1f} dB")
    lines.append(f"  Std Dev: {energy['std_energy_db']:.1f} dB")
    lines.append(f"  Range: {energy['min_energy_db']:.1f} to {energy['max_energy_db']:.1f} dB")

    # Pitch
    lines.append("\n" + "=" * 60)
    lines.append("PITCH")
    lines.append("=" * 60)
    pitch = results["pitch"]
    if pitch["mean_pitch_hz"] > 0:
        lines.append(f"  Mean: {pitch['mean_pitch_hz']:.1f} Hz")
        lines.append(f"  Std Dev: {pitch['std_pitch_hz']:.1f} Hz")
        lines.append(
            f"  Range: {pitch['min_pitch_hz']:.1f} to {pitch['max_pitch_hz']:.1f} Hz"
        )
    else:
        lines.append("  (No pitched sound detected)")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)


@app.command()
def analyze(
    file: Path = typer.Argument(  # noqa: B008
        ..., help="Path to .webm audio file", exists=True
    ),
):
    """
    [MVP0 LEGACY] Analyze a .webm audio file for speaking metrics.

    This is the MVP0 analysis command. Use 'practice' for the full MVP1 experience.
    """
    try:
        # Load audio using AudioLoader
        console.print(f"[cyan]Analyzing:[/cyan] {file}")
        console.print()

        loader = AudioLoader(sample_rate=16000)
        audio_data, sample_rate = loader.load(file)
        duration = len(audio_data) / sample_rate

        console.print(f"✓ Audio loaded ({duration:.2f}s, {sample_rate} Hz)")
        console.print()
        console.print("Running analysis...")

        # Run all analyzers
        analyzer = ClarityAnalyzer()
        results = analyzer.analyze(audio_data, sample_rate)

        # Print formatted results
        console.print()
        console.print(format_results(results))

        # Save to CSV log
        console.print()
        logger = CSVLogger()
        logger.log(str(file), results)
        console.print(f"✓ Results logged to: {logger.csv_path}")

        raise typer.Exit(0)

    except FFmpegNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1) from e
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]", file=sys.stderr)
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise typer.Exit(1) from e


@app.command()
def report():
    """
    [MVP0 LEGACY] Generate a progress report from logged sessions.

    This is the MVP0 reporting command. Use 'history' and 'weekly' for MVP1 features.
    """
    try:
        # Read CSV log
        logger = CSVLogger()
        sessions = logger.read_all()

        if not sessions:
            console.print(
                "[yellow]No sessions logged yet. Run 'clarity analyze' first.[/yellow]",
                file=sys.stderr,
            )
            raise typer.Exit(1)

        console.print(f"Generating report from {len(sessions)} sessions...")

        # Generate plot
        plotter = MetricsPlotter()
        plot_path = "metrics_plot.png"
        plotter.plot_metrics(sessions, plot_path)

        # Generate markdown report
        report_gen = ReportGenerator()
        report_path = "clarity_report.md"
        report_gen.generate(sessions, report_path, plot_path)

        console.print()
        console.print("✓ Report generation complete!")
        console.print(f"  - Markdown: {report_path}")
        console.print(f"  - Plot: {plot_path}")

        raise typer.Exit(0)

    except Exception as e:
        console.print(f"[red]Error generating report: {e}[/red]", file=sys.stderr)
        import traceback
        traceback.print_exc()
        raise typer.Exit(1) from e


# ============================================================================
# Main entry point
# ============================================================================


def main():
    """Main entry point for the Clarity CLI."""
    app()


if __name__ == "__main__":
    main()
