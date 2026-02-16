"""
Main entry point for the Clarity CLI.

Usage:
    python -m clarity --help
    python -m clarity analyze <file.webm>
"""

import argparse
import sys
from pathlib import Path

from clarity.analyzers.analyzer import ClarityAnalyzer
from clarity.audio_loader import AudioLoader, FFmpegNotFoundError


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


def cmd_analyze(args: argparse.Namespace) -> int:
    """
    Handle the 'analyze' subcommand.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    file_path = Path(args.file)

    # Validate file exists
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    # Validate file extension
    if file_path.suffix.lower() != ".webm":
        print(
            f"Warning: Expected .webm file, got {file_path.suffix}. Attempting to load anyway...",
            file=sys.stderr,
        )

    try:
        # Load audio using AudioLoader
        print(f"Analyzing: {file_path}")
        print()

        loader = AudioLoader(sample_rate=16000)
        audio_data, sample_rate = loader.load(file_path)
        duration = len(audio_data) / sample_rate

        print(f"✓ Audio loaded ({duration:.2f}s, {sample_rate} Hz)")
        print()
        print("Running analysis...")

        # Run all analyzers
        analyzer = ClarityAnalyzer()
        results = analyzer.analyze(audio_data, sample_rate)

        # Print formatted results
        print()
        print(format_results(results))

        return 0

    except FFmpegNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


def main() -> int:
    """Main entry point for the Clarity CLI."""
    parser = argparse.ArgumentParser(
        prog="clarity",
        description="Speaking clarity practice tool - analyze audio for speaking metrics",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a .webm audio file for speaking metrics",
    )
    analyze_parser.add_argument(
        "file",
        help="Path to .webm audio file",
    )

    args = parser.parse_args()

    if args.command == "analyze":
        return cmd_analyze(args)
    elif args.command is None:
        parser.print_help()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
