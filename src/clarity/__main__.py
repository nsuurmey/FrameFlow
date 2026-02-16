"""
Main entry point for the Clarity CLI.

Usage:
    python -m clarity --help
    python -m clarity analyze <file.webm>
"""

import argparse
import sys


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

    # analyze command (placeholder for Epic 0.2)
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
        print(f"[Placeholder] Would analyze: {args.file}")
        print("Analysis pipeline not yet implemented (Epic 0.2)")
        return 0
    elif args.command is None:
        parser.print_help()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
