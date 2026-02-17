"""
Tests for analysis engine (Epic 1.4).

Tests Claude API client, prompt assembly, and response parsing.
"""

from unittest.mock import patch

import pytest

from clarity.analysis import (
    AnalysisResult,
    ClaudeAPIClient,
    DimensionScore,
    Tip,
    build_analysis_prompt,
    parse_analysis_response,
    validate_analysis_response,
)
from clarity.config import ConfigManager
from clarity.session import Framework, Phase, get_phase_config

# ===== API Client Tests =====


def test_client_requires_api_key():
    """Test that client raises error when API key is missing."""
    with patch.object(ConfigManager, "get_api_key", return_value=None):
        with pytest.raises(ValueError, match="API key is required"):
            ClaudeAPIClient()


def test_client_accepts_api_key_parameter():
    """Test client initialization with API key parameter."""
    client = ClaudeAPIClient(api_key="test-key-123")
    assert client.client.api_key == "test-key-123"


def test_client_fetches_api_key_from_config():
    """Test client fetches API key from config."""
    with patch.object(ConfigManager, "get_api_key", return_value="config-key-456"):
        client = ClaudeAPIClient()
        assert client.client.api_key == "config-key-456"


def test_client_timeout_parameter():
    """Test client timeout configuration."""
    client = ClaudeAPIClient(api_key="test-key", timeout=45.0)
    assert client.timeout == 45.0


def test_client_max_retries_parameter():
    """Test client max retries configuration."""
    client = ClaudeAPIClient(api_key="test-key", max_retries=5)
    assert client.max_retries == 5


# ===== Model Tests =====


def test_dimension_score_dataclass():
    """Test DimensionScore structure."""
    score = DimensionScore(
        dimension="Filler Frequency",
        score=75,
        rating="Strong",
        feedback="Good filler control",
    )

    assert score.dimension == "Filler Frequency"
    assert score.score == 75
    assert score.rating == "Strong"
    assert score.feedback == "Good filler control"


def test_tip_dataclass():
    """Test Tip structure."""
    tip = Tip(
        title="Replace fillers with pauses",
        explanation="Use silence instead of um/uh",
        transcript_excerpt="um, so like, the thing is",
        technique="Box breathing",
    )

    assert tip.title == "Replace fillers with pauses"
    assert tip.explanation == "Use silence instead of um/uh"
    assert tip.transcript_excerpt == "um, so like, the thing is"
    assert tip.technique == "Box breathing"


def test_analysis_result_dataclass():
    """Test AnalysisResult structure."""
    result = AnalysisResult(
        dimension_scores=[],
        composite_score=75,
        tips=[],
        framework_used="PREP",
        framework_completion=True,
        missing_components=[],
        filler_count=12,
        filler_rate=4.5,
        filler_percentage=3.2,
        word_count=375,
        duration_seconds=160.0,
        speaking_rate_wpm=140.6,
    )

    assert result.composite_score == 75
    assert result.filler_count == 12
    assert result.speaking_rate_wpm == 140.6


# ===== Response Parsing Tests =====


@pytest.fixture
def sample_response():
    """Sample Claude API response."""
    return {
        "dimension_scores": [
            {
                "dimension": "Filler Frequency",
                "score": 75,
                "rating": "Strong",
                "feedback": "Good filler control with only 4.5/min",
            },
            {
                "dimension": "Structural Clarity",
                "score": 85,
                "rating": "Strong",
                "feedback": "All PREP components present",
            },
        ],
        "composite_score": 80,
        "tips": [
            {
                "title": "Replace fillers with pauses",
                "explanation": "Use deliberate silence instead of um/uh",
                "transcript_excerpt": "um, the main point is",
                "technique": "Box breathing before speaking",
            },
            {
                "title": "Strengthen your opening",
                "explanation": "Lead with main point upfront",
                "transcript_excerpt": None,
                "technique": "BLUF (Bottom Line Up Front)",
            },
        ],
        "framework_analysis": {
            "framework_used": "PREP",
            "completion": True,
            "missing_components": [],
        },
        "filler_count": 12,
        "filler_rate": 4.5,
        "filler_percentage": 3.2,
        "word_count": 375,
        "duration_seconds": 160,
        "speaking_rate_wpm": 140.6,
        "maze_count": 2,
        "maze_rate": 0.75,
    }


def test_parse_analysis_response(sample_response):
    """Test parsing valid Claude response."""
    result = parse_analysis_response(sample_response)

    assert isinstance(result, AnalysisResult)
    assert result.composite_score == 80
    assert len(result.dimension_scores) == 2
    assert len(result.tips) == 2
    assert result.filler_count == 12
    assert result.framework_used == "PREP"


def test_parse_dimension_scores(sample_response):
    """Test parsing dimension scores."""
    result = parse_analysis_response(sample_response)

    assert result.dimension_scores[0].dimension == "Filler Frequency"
    assert result.dimension_scores[0].score == 75
    assert result.dimension_scores[0].rating == "Strong"
    assert "filler control" in result.dimension_scores[0].feedback


def test_parse_tips(sample_response):
    """Test parsing tips."""
    result = parse_analysis_response(sample_response)

    assert result.tips[0].title == "Replace fillers with pauses"
    assert "silence" in result.tips[0].explanation
    assert result.tips[0].technique == "Box breathing before speaking"


def test_parse_optional_metrics(sample_response):
    """Test parsing optional phase-specific metrics."""
    result = parse_analysis_response(sample_response)

    assert result.maze_count == 2
    assert result.maze_rate == 0.75


def test_validate_analysis_response_valid(sample_response):
    """Test validation passes for valid response."""
    errors = validate_analysis_response(sample_response)
    assert len(errors) == 0


def test_validate_analysis_response_missing_field():
    """Test validation catches missing required fields."""
    response = {"composite_score": 75}  # Missing most fields

    errors = validate_analysis_response(response)
    assert len(errors) > 0
    assert any("dimension_scores" in err for err in errors)


def test_validate_analysis_response_invalid_score():
    """Test validation catches invalid scores."""
    response = {
        "dimension_scores": [
            {"dimension": "Test", "score": 150, "rating": "Excellent", "feedback": "Good"}
        ],
        "composite_score": 75,
        "tips": [],
        "filler_count": 0,
        "filler_rate": 0.0,
        "filler_percentage": 0.0,
        "word_count": 100,
        "duration_seconds": 60,
        "speaking_rate_wpm": 100,
    }

    errors = validate_analysis_response(response)
    assert any("invalid score" in err for err in errors)


def test_validate_analysis_response_invalid_composite():
    """Test validation catches invalid composite score."""
    response = {
        "dimension_scores": [],
        "composite_score": -10,  # Invalid
        "tips": [],
        "filler_count": 0,
        "filler_rate": 0.0,
        "filler_percentage": 0.0,
        "word_count": 100,
        "duration_seconds": 60,
        "speaking_rate_wpm": 100,
    }

    errors = validate_analysis_response(response)
    assert any("composite_score" in err for err in errors)


# ===== Prompt Building Tests =====


def test_build_analysis_prompt_phase1():
    """Test prompt building for Phase 1."""
    config = get_phase_config(Phase.PHASE_1)
    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test transcript",
    )

    # Should include Phase 1 dimensions
    assert "Filler Frequency" in prompt
    assert "Structural Clarity" in prompt

    # Should NOT include Phase 2+ dimensions
    assert "Conceptual Precision" not in prompt
    assert "Hedging Control" not in prompt

    # Should include framework definition
    assert "PREP" in prompt
    assert "Point" in prompt

    # Should include filler lexicon
    assert "um" in prompt or "uh" in prompt


def test_build_analysis_prompt_phase2():
    """Test prompt building for Phase 2."""
    config = get_phase_config(Phase.PHASE_2)
    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test transcript",
    )

    # Should include Phase 2 dimensions
    assert "Conceptual Precision" in prompt
    assert "Hedging Control" in prompt

    # Should include hedging lexicon
    assert "kind of" in prompt or "sort of" in prompt


def test_build_analysis_prompt_phase3():
    """Test prompt building for Phase 3."""
    config = get_phase_config(Phase.PHASE_3)
    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test transcript",
    )

    # Should include all dimensions
    assert "Filler Frequency" in prompt
    assert "Vocal Delivery" in prompt


def test_build_analysis_prompt_includes_baseline():
    """Test prompt includes baseline context."""
    config = get_phase_config(Phase.PHASE_1)
    baseline = {"filler_rate": 8.5, "speaking_rate_wpm": 145}

    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test",
        baseline_metrics=baseline,
    )

    assert "Baseline" in prompt
    assert "8.5" in prompt


def test_build_analysis_prompt_includes_recent_metrics():
    """Test prompt includes recent performance context."""
    config = get_phase_config(Phase.PHASE_1)
    recent = [
        {"filler_rate": 6.5},
        {"filler_rate": 5.8},
        {"filler_rate": 6.2},
    ]

    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test",
        recent_metrics=recent,
    )

    assert "Recent Performance" in prompt or "last 5 sessions" in prompt


def test_build_analysis_prompt_output_format():
    """Test prompt includes JSON output format."""
    config = get_phase_config(Phase.PHASE_1)
    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test",
    )

    assert "JSON" in prompt
    assert "dimension_scores" in prompt
    assert "composite_score" in prompt


def test_build_analysis_prompt_framework_definition():
    """Test prompt includes framework components."""
    config = get_phase_config(Phase.PHASE_1)
    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test",
    )

    # PREP components
    assert "Point" in prompt
    assert "Reason" in prompt
    assert "Example" in prompt


# ===== Integration Tests =====


def test_full_parse_flow(sample_response):
    """Test complete flow: validate → parse → access."""
    # Validate
    errors = validate_analysis_response(sample_response)
    assert len(errors) == 0

    # Parse
    result = parse_analysis_response(sample_response)

    # Access data
    assert result.composite_score == 80
    assert result.dimension_scores[0].score == 75
    assert result.tips[0].title == "Replace fillers with pauses"


def test_prompt_contains_all_required_sections():
    """Test prompt has all necessary sections."""
    config = get_phase_config(Phase.PHASE_2)
    prompt = build_analysis_prompt(
        phase_config=config,
        framework=Framework.PREP,
        transcript="Test",
    )

    required_sections = [
        "Scoring Rubric",
        "Filler Words",
        "Framework",
        "Output Format",
        "JSON",
    ]

    for section in required_sections:
        assert section in prompt, f"Missing section: {section}"


def test_phase_progression_adds_dimensions():
    """Test that dimensions expand across phases."""
    phase1_prompt = build_analysis_prompt(
        get_phase_config(Phase.PHASE_1), Framework.PREP, "Test"
    )
    phase2_prompt = build_analysis_prompt(
        get_phase_config(Phase.PHASE_2), Framework.PREP, "Test"
    )
    phase3_prompt = build_analysis_prompt(
        get_phase_config(Phase.PHASE_3), Framework.PREP, "Test"
    )

    # Phase 3 should be longest (most dimensions)
    assert len(phase3_prompt) > len(phase2_prompt)
    assert len(phase2_prompt) > len(phase1_prompt)
