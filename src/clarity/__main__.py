"""
Main entry point for the Clarity CLI.

Usage:
    python -m clarity --help
    python -m clarity analyze <file.webm>
"""

import argparse
import sys
from pathlib import Path

from clarity.audio_loader import AudioLoader, FFmpegNotFoundError


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
        loader = AudioLoader(sample_rate=16000)
        print(f"Loading audio from: {file_path}")

        audio_data, sample_rate = loader.load(file_path)
        duration = len(audio_data) / sample_rate

        # Print basic info
        print("✓ Audio loaded successfully")
        print(f"  Duration: {duration:.2f} seconds")
        print(f"  Sample rate: {sample_rate} Hz")
        print(f"  Samples: {len(audio_data):,}")
        print()
        print("[Next steps] Analysis metrics not yet implemented (Epic 0.3)")

        return 0

    except FFmpegNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error loading audio: {e}", file=sys.stderr)
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
