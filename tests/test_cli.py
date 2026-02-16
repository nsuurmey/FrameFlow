"""Tests for the CLI entry point."""

import sys

from clarity.__main__ import main


def test_cli_help():
    """Test that --help flag works."""
    sys.argv = ["clarity", "--help"]
    try:
        main()
    except SystemExit as e:
        # --help causes sys.exit(0)
        assert e.code == 0


def test_cli_version():
    """Test that --version flag works."""
    sys.argv = ["clarity", "--version"]
    try:
        main()
    except SystemExit as e:
        # --version causes sys.exit(0)
        assert e.code == 0


def test_cli_no_args():
    """Test that running without arguments prints help and exits."""
    sys.argv = ["clarity"]
    result = main()
    assert result == 0


def test_analyze_placeholder():
    """Test that analyze command placeholder works."""
    sys.argv = ["clarity", "analyze", "dummy.webm"]
    result = main()
    assert result == 0
