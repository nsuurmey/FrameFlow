"""
Filler Fidelity Testing Script (Ticket 1.2.2).

Tests different Whisper model sizes (tiny, base, small, medium) against
recordings with deliberate fillers to determine preservation rates.

Usage:
    python tests/filler_fidelity_test.py <audio_dir>

Expected audio files in <audio_dir>:
- filler_sample_01.webm (known fillers: um, uh, like, so)
- filler_sample_02.webm (known fillers: um, you know, basically)
- filler_sample_03.webm (known fillers: uh, like, actually, kind of)
etc.

Each audio file should have a corresponding .txt file with ground truth:
- filler_sample_01.txt:
  ```
  um hello everyone uh this is like a test recording so yeah
  ```
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from clarity.transcription import WhisperService, detect_fillers
from clarity.transcription.metrics import FILLER_LEXICON


def load_ground_truth(audio_path: Path) -> dict[str, Any]:
    """
    Load ground truth from .txt file.

    Expected format:
    transcript with fillers preserved

    Optional .json file with:
    {
        "expected_fillers": ["um", "uh", "like"],
        "filler_count": 3
    }

    Args:
        audio_path: Path to audio file

    Returns:
        Dictionary with ground_truth_transcript and expected_fillers
    """
    txt_path = audio_path.with_suffix(".txt")
    json_path = audio_path.with_suffix(".json")

    result = {}

    if txt_path.exists():
        result["ground_truth_transcript"] = txt_path.read_text().strip()

    if json_path.exists():
        metadata = json.loads(json_path.read_text())
        result["expected_fillers"] = metadata.get("expected_fillers", [])
        result["filler_count"] = metadata.get("filler_count", 0)
    else:
        # Auto-detect fillers from ground truth transcript
        if "ground_truth_transcript" in result:
            words = result["ground_truth_transcript"].lower().split()
            fillers = [w for w in words if w in FILLER_LEXICON]
            result["expected_fillers"] = fillers
            result["filler_count"] = len(fillers)

    return result


def test_model(
    model_size: str,
    audio_path: Path,
    ground_truth: dict[str, Any],
    console: Console,
) -> dict[str, Any]:
    """
    Test a single Whisper model against an audio file.

    Args:
        model_size: Whisper model size
        audio_path: Path to audio file
        ground_truth: Ground truth data
        console: Rich console for output

    Returns:
        Dictionary with test results
    """
    console.print(f"  Testing {model_size} model...", style="cyan")

    try:
        # Initialize service
        service = WhisperService(model_size=model_size)

        # Transcribe
        result = service.transcribe_file(
            audio_path, show_progress=False
        )

        # Detect fillers
        filler_words, positions = detect_fillers(
            result.words, result.duration_seconds
        )

        detected_fillers = [w.word.lower() for w in filler_words]

        # Calculate preservation rate
        expected = set(ground_truth.get("expected_fillers", []))
        detected = set(detected_fillers)

        if expected:
            preserved = expected.intersection(detected)
            preservation_rate = len(preserved) / len(expected) * 100
            missed = expected - detected
            false_positives = detected - expected
        else:
            preservation_rate = 0.0
            missed = set()
            false_positives = detected

        return {
            "model_size": model_size,
            "transcript": result.transcript,
            "detected_filler_count": len(detected_fillers),
            "detected_fillers": detected_fillers,
            "expected_filler_count": len(expected),
            "preservation_rate": preservation_rate,
            "preserved_fillers": list(preserved),
            "missed_fillers": list(missed),
            "false_positives": list(false_positives),
            "success": True,
        }

    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
        return {
            "model_size": model_size,
            "success": False,
            "error": str(e),
        }


def test_all_models(
    audio_files: list[Path], console: Console
) -> dict[str, list[dict[str, Any]]]:
    """
    Test all model sizes against all audio files.

    Args:
        audio_files: List of audio file paths
        console: Rich console for output

    Returns:
        Dictionary mapping model_size -> list of results
    """
    models = ["tiny", "base", "small", "medium"]
    results_by_model = {model: [] for model in models}

    for audio_path in audio_files:
        console.print(f"\n[bold]Testing: {audio_path.name}[/bold]")

        # Load ground truth
        ground_truth = load_ground_truth(audio_path)

        if "ground_truth_transcript" in ground_truth:
            console.print(
                f"  Ground truth: {ground_truth['ground_truth_transcript'][:80]}..."
            )
            console.print(
                f"  Expected fillers: {ground_truth.get('expected_fillers', [])}"
            )

        # Test each model
        for model_size in models:
            result = test_model(model_size, audio_path, ground_truth, console)
            result["audio_file"] = audio_path.name
            results_by_model[model_size].append(result)

    return results_by_model


def generate_report(
    results_by_model: dict[str, list[dict[str, Any]]], console: Console
) -> None:
    """
    Generate summary report and comparison table.

    Args:
        results_by_model: Results organized by model size
        console: Rich console for output
    """
    console.print("\n" + "=" * 70)
    console.print("[bold cyan]Filler Fidelity Test Results[/bold cyan]")
    console.print("=" * 70 + "\n")

    # Create comparison table
    table = Table(title="Model Comparison")
    table.add_column("Model", style="cyan")
    table.add_column("Avg Preservation Rate", justify="right")
    table.add_column("Avg Detected", justify="right")
    table.add_column("False Positives", justify="right")
    table.add_column("Test Count", justify="right")

    for model_size in ["tiny", "base", "small", "medium"]:
        results = results_by_model[model_size]
        successful = [r for r in results if r.get("success", False)]

        if not successful:
            table.add_row(model_size, "N/A", "N/A", "N/A", "0")
            continue

        avg_preservation = sum(
            r["preservation_rate"] for r in successful
        ) / len(successful)
        avg_detected = sum(
            r["detected_filler_count"] for r in successful
        ) / len(successful)
        total_false_positives = sum(
            len(r.get("false_positives", [])) for r in successful
        )

        table.add_row(
            model_size,
            f"{avg_preservation:.1f}%",
            f"{avg_detected:.1f}",
            str(total_false_positives),
            str(len(successful)),
        )

    console.print(table)

    # Recommendation
    console.print("\n[bold]Recommendations:[/bold]")
    best_models = []
    for model_size in ["tiny", "base", "small", "medium"]:
        results = [r for r in results_by_model[model_size] if r.get("success")]
        if results:
            avg_rate = sum(r["preservation_rate"] for r in results) / len(results)
            if avg_rate >= 80:
                best_models.append((model_size, avg_rate))

    if best_models:
        console.print("\nModels with ≥80% filler preservation:")
        for model, rate in best_models:
            console.print(f"  • {model}: {rate:.1f}%")

        best_model = max(best_models, key=lambda x: x[1])
        console.print(f"\n[green]✓ Recommended default: {best_model[0]}[/green]")
    else:
        console.print("\n[yellow]⚠ No model achieved ≥80% preservation[/yellow]")
        console.print("Consider using 'medium' or 'large' for better fidelity.")


def save_results(
    results_by_model: dict[str, list[dict[str, Any]]], output_path: Path
) -> None:
    """
    Save detailed results to JSON file.

    Args:
        results_by_model: Test results
        output_path: Path to save results
    """
    with output_path.open("w") as f:
        json.dump(results_by_model, f, indent=2)


def main():
    """Main entry point for filler fidelity testing."""
    parser = argparse.ArgumentParser(
        description="Test Whisper model filler fidelity"
    )
    parser.add_argument(
        "audio_dir",
        type=Path,
        help="Directory containing audio samples with ground truth",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/whisper_fidelity_results.json"),
        help="Output path for results JSON",
    )

    args = parser.parse_args()

    console = Console()

    # Find audio files
    audio_dir = args.audio_dir
    if not audio_dir.exists():
        console.print(f"[red]Error: Directory not found: {audio_dir}[/red]")
        sys.exit(1)

    audio_files = list(audio_dir.glob("*.webm")) + list(audio_dir.glob("*.wav"))

    if not audio_files:
        console.print(f"[red]Error: No audio files found in {audio_dir}[/red]")
        console.print("\nExpected files:")
        console.print("  - filler_sample_01.webm (with filler_sample_01.txt)")
        console.print("  - filler_sample_02.webm (with filler_sample_02.txt)")
        console.print("  - etc.")
        sys.exit(1)

    console.print(f"\n[bold]Found {len(audio_files)} audio files[/bold]")

    # Test all models
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Running fidelity tests...", total=None)
        results = test_all_models(audio_files, console)

    # Generate report
    generate_report(results, console)

    # Save results
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_results(results, args.output)
    console.print(f"\n✓ Detailed results saved to: {args.output}")


if __name__ == "__main__":
    main()
